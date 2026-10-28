"""Export an allowlisted public project; never include uploaded/private data."""
import argparse,hashlib,shutil,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROOT_FILES=['SKILL.md','README.md','README.zh-CN.md','LICENSE','requirements.txt','requirements.lock.txt','run_report.py','VALIDATION.md','.gitignore']
FOLDERS={'scripts':['analyze.py','appendix.py','evaluate.py','pricing.py','export_project.py','test_analysis.py','test_appendix.py','test_evaluate.py','test_pricing.py','test_release.py'],'references':['appendix.md','evaluation.md','installation.md','methodology.md','pricing.md'],'agents':['openai.yaml'],'examples':['DATA.md','generate_demo.py','sample-report.html','synthetic_excess.csv','synthetic_total.csv'],'.github/workflows':['test.yml']}
def export(destination):
    dst=Path(destination).resolve()
    if dst.exists():raise ValueError('Choose a new destination folder')
    if dst==ROOT or ROOT in dst.parents:raise ValueError('Export outside the source skill directory')
    files=[ROOT/x for x in ROOT_FILES]
    for folder,names in FOLDERS.items():
        files.extend(ROOT/folder/name for name in names)
    for p in files:
        if not p.is_file():raise ValueError(f'Missing release file {p.name}')
    dst.mkdir(parents=True)
    for p in files:
        target=dst/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    manifest=[]
    for p in sorted(dst.rglob('*')):
        if p.is_file():manifest.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(dst).as_posix())
    (dst/'SHA256SUMS').write_text('\n'.join(manifest)+'\n')
    archive=Path(str(dst)+'.tar.gz')
    if archive.exists():raise ValueError('Archive already exists')
    with tarfile.open(archive,'w:gz') as t:
        for p in sorted(dst.rglob('*')):
            if p.is_file():t.add(p,arcname=(Path(dst.name)/p.relative_to(dst)).as_posix(),recursive=False)
    print('Public project:',dst);print('Archive:',archive);print('Files:',len(manifest)+1)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('destination');export(p.parse_args().destination)
