"""Install the small, Apache-2.0 SmolVLM model into this project only."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import zipfile
import requests

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.local-ai'
REPO = 'ggml-org/SmolVLM-256M-Instruct-GGUF'
RELEASE = 'b12138'


def main():
    DEST.mkdir(exist_ok=True)
    release = requests.get(f'https://api.github.com/repos/ggml-org/llama.cpp/releases/tags/{RELEASE}', timeout=30)
    release.raise_for_status()
    asset = next(a for a in release.json()['assets'] if a['name'].endswith('bin-win-cpu-x64.zip'))
    metadata = requests.get(f'https://huggingface.co/api/models/{REPO}', timeout=30)
    metadata.raise_for_status()
    revision = metadata.json()['sha']
    files = requests.get(f'https://huggingface.co/api/models/{REPO}/tree/{revision}', timeout=30)
    files.raise_for_status()
    names = ['SmolVLM-256M-Instruct-Q8_0.gguf', 'mmproj-SmolVLM-256M-Instruct-Q8_0.gguf']
    jobs = [(asset['name'], asset['browser_download_url'], asset['digest'].removeprefix('sha256:'))]
    for name in names:
        entry = next(f for f in files.json() if f['path'] == name)
        jobs.append((name, f'https://huggingface.co/{REPO}/resolve/{revision}/{name}', entry['lfs']['oid']))
    def download(job):
        name, url, expected = job
        target = DEST / name
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
            print(f'Already verified: {name}', flush=True)
            return
        temporary = target.with_suffix(target.suffix + '.part')
        digest = hashlib.sha256()
        with requests.get(url, stream=True, timeout=(15, 120)) as response:
            response.raise_for_status()
            with temporary.open('wb') as stream:
                for chunk in response.iter_content(1024 * 1024):
                    stream.write(chunk)
                    digest.update(chunk)
        if digest.hexdigest() != expected:
            raise RuntimeError(f'Checksum verification failed: {name}')
        temporary.replace(target)
        print(f'Downloaded and verified: {name} ({target.stat().st_size // 1000000} MB)', flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(download, jobs))
    runtime = DEST / 'runtime'
    runtime.mkdir(exist_ok=True)
    with zipfile.ZipFile(DEST / asset['name']) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            # Extract flat filenames only; no archive-supplied paths are executed.
            (runtime / Path(item.filename).name).write_bytes(archive.read(item))
    (DEST / 'manifest.json').write_text(json.dumps({'runtime_release': RELEASE, 'model_repo': REPO,
        'model_revision': revision, 'checksums': {j[0]:j[2] for j in jobs},
        'model_license': 'Apache-2.0', 'runtime_license': 'MIT'}, indent=2))
    print('Local vision files are ready. Start with start-local-ai.ps1.', flush=True)


if __name__ == '__main__':
    main()
