"""Serve only this preview directory on the local loopback interface."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from functools import partial
import argparse

ROOT=Path(__file__).resolve().parent

class PreviewHandler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        translated=Path(super().translate_path(path)).resolve()
        if not translated.is_relative_to(ROOT) or any(p.startswith('.') for p in translated.relative_to(ROOT).parts):
            return str(ROOT/'.not-served')
        return str(translated)
    def list_directory(self,path):
        self.send_error(403,'Directory listing disabled')
        return None

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=4204);args=p.parse_args()
    handler=partial(PreviewHandler,directory=str(ROOT))
    with ThreadingHTTPServer(('127.0.0.1',args.port),handler) as server:
        print(f'Ade 3D preview: http://127.0.0.1:{server.server_port}/',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass


