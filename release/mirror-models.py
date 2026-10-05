from pathlib import Path
import hashlib,json,zipfile,subprocess,urllib.request,os,time
root=Path('model-output');root.mkdir(exist_ok=True)
source=json.loads(Path('release/model-build-input.json').read_text(encoding='utf-8'))
result={'schema':1,'models':{}}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
for key,spec in source['models'].items():
 folder=root/key;folder.mkdir(exist_ok=True)
 for name,entry in spec['files'].items():
  target=folder/name
  if name=='LICENSE':target.write_bytes(source['license'].encode('utf-8'))
  else:
   url='https://modelscope.cn/models/'+spec['model']+'/resolve/'+spec['revision']+'/'+name
   for attempt in range(3):
    try:
     urllib.request.urlretrieve(url,target)
     break
    except Exception:
     if attempt==2:raise
     time.sleep(5)
  assert target.stat().st_size==entry['bytes'],name
  assert sha(target)==entry['sha256'],name
  print('Verified',key,name,flush=True)
 archive=root/spec['archive']
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for name in spec['files']:z.write(folder/name,name)
  z.writestr('SOURCE.txt',spec['model']+'\nRevision: '+spec['revision']+'\nLicense: Apache-2.0\nUnmodified weights.\n')
 spec['sha256']=sha(archive);spec['bytes']=archive.stat().st_size
 assert spec['bytes']<2*1024**3
 result['models'][key]=spec
 subprocess.run(['gh','release','upload','models-20261005',str(archive),'--repo',os.environ['GITHUB_REPOSITORY']],check=True)
(root/'model-downloads.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
subprocess.run(['gh','release','upload','models-20261005',str(root/'model-downloads.json'),'--clobber','--repo',os.environ['GITHUB_REPOSITORY']],check=True)
