#!/usr/bin/env python3
"""
SyncExtPack Web Builder
A simple web interface for building Ford SYNC 2 custom app packages.
"""

import os
import sys
import uuid
import threading
import shutil
import logging
import requests
from datetime import datetime

from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)

# ── Configuration ──────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILDS_DIR = os.path.join(SCRIPT_DIR, 'builds')
os.makedirs(BUILDS_DIR, exist_ok=True)

MAGIC_NUM = '0'  # 0 = no expiration

# Cloudflare Turnstile
TURNSTILE_SITE_KEY = '0x4AAAAAAD7JVZxpkS-7qcFX'
TURNSTILE_SECRET = os.environ.get('TURNSTILE_SECRET', '')
TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'

# Allowed app names (whitelist)
ALLOWED_APPS = {
    'AutoKit', 'MirrorLink_EN_NEW', 'MirrorLink_NEW',
    'Explorer', 'Player_EN', 'Player',
    'Navitel', 'Reboot',
}

# Mutual exclusivity groups: pick at most one from each group
MUTEX_GROUPS = [
    {'MirrorLink_EN_NEW', 'MirrorLink_NEW'},
    {'Player_EN', 'Player'},
]

# ── Job tracking ───────────────────────────────────────────────────────────
jobs = {}  # job_id -> {status, message, zip_path, log}
jobs_lock = threading.Lock()
JOB_TTL = 3600  # Auto-cleanup jobs older than 1 hour (seconds)

def cleanup_old_jobs():
    """Remove finished/failed jobs older than JOB_TTL to prevent memory leak."""
    now = datetime.utcnow()
    to_remove = []
    with jobs_lock:
        for jid, job in jobs.items():
            if job['status'] in ('done', 'failed'):
                created = job.get('created_at')
                if created and (now - created).total_seconds() > JOB_TTL:
                    to_remove.append(jid)
        for jid in to_remove:
            job = jobs.pop(jid, None)
            if job and job.get('job_dir'):
                try:
                    shutil.rmtree(job['job_dir'])
                except Exception:
                    pass


import re

def validate_serial(serial):
    """Validate APIM serial number: 8 alphanumeric chars, no letter 'O'."""
    if not serial or len(serial) != 8:
        return False
    if 'O' in serial.upper():
        return False
    # Only allow A-Z (except O) and 0-9 to prevent path traversal
    if not re.match(r'^[A-NP-Z0-9]+$', serial):
        return False
    return True


def verify_turnstile(token, client_ip):
    """Call Cloudflare Turnstile siteverify to validate the token."""
    if not TURNSTILE_SECRET:
        return False, 'Turnstile secret not configured on server'
    try:
        resp = requests.post(TURNSTILE_VERIFY_URL, data={
            'secret': TURNSTILE_SECRET,
            'response': token,
            'remoteip': client_ip,
        }, timeout=10)
        result = resp.json()
        if result.get('success'):
            return True, None
        else:
            err_codes = result.get('error-codes', [])
            return False, f'Turnstile verification failed: {err_codes}'
    except Exception as e:
        return False, f'Turnstile verification error: {str(e)}'


def run_build(job_id, serial, apps):
    """Run the build process in a background thread using direct Python calls."""
    job_dir = os.path.join(BUILDS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    with jobs_lock:
        jobs[job_id]['status'] = 'building'
        jobs[job_id]['message'] = 'Building...'

    log_lines = []

    def log(msg):
        ts = datetime.now().strftime('%H:%M:%S')
        line = f'[{ts}] {msg}'
        log_lines.append(line)
        with jobs_lock:
            jobs[job_id]['log'] = '\n'.join(log_lines)
        app.logger.info(msg)

    from builder.build import Build
    from build_installer import PackCompiler
    from build_archive import genArchive, cleanupResult

    try:
        # Step 1: Build install pack
        apps_str = ', '.join(apps)
        log(f'Step 1/4: Building install pack ({apps_str})...')
        build = Build(serial)
        result = build.buildPack('SyncExtPack/pack_install.bin', MAGIC_NUM, apps, work_dir=job_dir)
        if result is None:
            log('  ERROR: buildPack failed (invalid serial or no valid units)')
            with jobs_lock:
                jobs[job_id]['status'] = 'failed'
                jobs[job_id]['message'] = 'Build failed at step 1'
            return
        log('  OK')

        # Step 2: Build update service pack
        log('Step 2/4: Building update service pack...')
        build2 = Build(serial)
        result2 = build2.buildPack('SyncExtPack/update.bin', MAGIC_NUM, ['UpdateService'], work_dir=job_dir)
        if result2 is None:
            log('  ERROR: UpdateService buildPack failed')
            with jobs_lock:
                jobs[job_id]['status'] = 'failed'
                jobs[job_id]['message'] = 'Build failed at step 2'
            return
        log('  OK')

        # Step 3: Build installer
        log('Step 3/4: Building installer (swfmill + secureSWF)...')
        pc = PackCompiler()
        pc.start(serial, work_dir=job_dir)
        pc.cleanup()
        installer_path = os.path.join(job_dir, 'SyncExtPack', serial, 'SyncExtPack', 'Installer.jpg')
        if not os.path.exists(installer_path):
            log('  ERROR: Installer.jpg not found after build')
            with jobs_lock:
                jobs[job_id]['status'] = 'failed'
                jobs[job_id]['message'] = 'Build failed at step 3'
            return
        log('  OK')

        # Step 4: Archive
        log('Step 4/4: Creating ZIP archive...')
        result_dir, archive_path = genArchive(serial, work_dir=job_dir)
        cleanupResult(result_dir)
        if not os.path.exists(archive_path):
            log('  ERROR: ZIP file not found after archive')
            with jobs_lock:
                jobs[job_id]['status'] = 'failed'
                jobs[job_id]['message'] = 'Build failed at step 4'
            return
        log('  OK')

        zip_name = os.path.basename(archive_path)
        log(f'Build complete: {zip_name}')
        with jobs_lock:
            jobs[job_id]['status'] = 'done'
            jobs[job_id]['message'] = 'Build complete'
            jobs[job_id]['zip_path'] = archive_path
            jobs[job_id]['zip_name'] = zip_name
            jobs[job_id]['job_dir'] = job_dir

    except Exception as e:
        app.logger.exception(f'Build {job_id} failed')
        log('ERROR: Unexpected build failure')
        with jobs_lock:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['message'] = 'Build error'


# ── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', turnstile_site_key=TURNSTILE_SITE_KEY)


@app.route('/build', methods=['POST'])
def build():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request'}), 400

    # Turnstile verification
    turnstile_token = data.get('turnstile_token', '')
    client_ip = request.remote_addr or ''
    if request.headers.get('X-Forwarded-For'):
        client_ip = request.headers['X-Forwarded-For'].split(',')[0].strip()

    ok, err = verify_turnstile(turnstile_token, client_ip)
    if not ok:
        return jsonify({'error': err}), 403

    serial = (data.get('serial') or '').strip().upper()
    apps = data.get('apps') or []

    # Validate serial
    if not validate_serial(serial):
        return jsonify({'error': 'Invalid serial number. Must be 8 characters, no letter O.'}), 400

    # Validate apps
    if not apps:
        return jsonify({'error': 'Please select at least one app.'}), 400

    for a in apps:
        if a not in ALLOWED_APPS:
            return jsonify({'error': f'Unknown app: {a}'}), 400

    # Check mutual exclusivity
    for group in MUTEX_GROUPS:
        selected = group & set(apps)
        if len(selected) > 1:
            return jsonify({'error': 'Cannot select both EN and non-EN versions of the same app.'}), 400

    # Clean up old jobs to prevent memory leak
    cleanup_old_jobs()

    # Start build
    job_id = str(uuid.uuid4())[:8]
    with jobs_lock:
        jobs[job_id] = {
            'status': 'queued',
            'message': 'Queued',
            'zip_path': None,
            'zip_name': None,
            'log': '',
            'serial': serial,
            'apps': apps,
            'job_dir': None,
            'created_at': datetime.utcnow(),
        }

    thread = threading.Thread(target=run_build, args=(job_id, serial, apps), daemon=True)
    thread.start()

    return jsonify({'job_id': job_id})


@app.route('/status/<job_id>')
def status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        return jsonify({
            'status': job['status'],
            'message': job['message'],
            'log': job.get('log', ''),
            'zip_name': job.get('zip_name'),
        })


@app.route('/download/<job_id>')
def download(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job or job['status'] != 'done' or not job.get('zip_path'):
            return jsonify({'error': 'File not ready'}), 404
        zip_path = job['zip_path']
        zip_name = job['zip_name']

    if not os.path.exists(zip_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(zip_path, as_attachment=True, download_name=zip_name)


@app.route('/cleanup/<job_id>', methods=['DELETE'])
def cleanup(job_id):
    with jobs_lock:
        job = jobs.pop(job_id, None)
    if job and job.get('job_dir'):
        try:
            shutil.rmtree(job['job_dir'])
        except:
            pass
    return jsonify({'ok': True})


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(levelname)s: %(message)s')
    app.run(host='0.0.0.0', port=5000, debug=False)
