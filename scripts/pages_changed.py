"""Durable deployment digest on isolated branch; updated only after deploy succeeds."""
import json,subprocess

def gh(path, body=None):
    args=['gh','api',path]
    if body is not None:args+=['--method','POST','--input','-']
    r=subprocess.run(args,input=json.dumps(body) if body is not None else None,text=True,capture_output=True)
    if r.returncode:
        if 'HTTP 404' in r.stderr:return None
        raise RuntimeError('github_deployment_state_read_or_write_failed')
    return json.loads(r.stdout)

def changed(repo,current):
    state=gh(f'repos/{repo}/git/ref/heads/pages-deployment-state')
    if state is None:return True
    commit=gh(f'repos/{repo}/git/commits/'+state['object']['sha'])
    return commit['message'].splitlines()[0]!='pages-public-sha256:'+current

def record(repo,digest):
    if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('invalid_digest')
    root=f'repos/{repo}/git/'
    old=gh(root+'ref/heads/pages-deployment-state')
    tree=gh(root+'trees',{'tree':[{'path':'public-digest.txt','mode':'100644','type':'blob','content':digest+'\n'}]})
    commit=gh(root+'commits',{'message':'pages-public-sha256:'+digest,'tree':tree['sha'],'parents':[old['object']['sha']] if old else []})
    if old:
        # Fast-forward-only prevents silently overwriting concurrent state.
        args=['gh','api',root+'refs/heads/pages-deployment-state','--method','PATCH','--input','-']
        subprocess.run(args,input=json.dumps({'sha':commit['sha'],'force':False}),text=True,check=True,stdout=subprocess.DEVNULL)
    else:gh(root+'refs',{'ref':'refs/heads/pages-deployment-state','sha':commit['sha']})

if __name__=='__main__':
    import sys
    if sys.argv[1]=='record':record(sys.argv[2],sys.argv[3])
    else:print('true' if changed(sys.argv[1],sys.argv[2]) else 'false')
