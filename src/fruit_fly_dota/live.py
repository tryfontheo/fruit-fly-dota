"""Local Workshop transport. Untrained full-connectome smoke policy, not Dota AI."""
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import numpy as np
from .malecns import load_full
from .full_neural import FullReservoir

OBS_SIZE = 16
ACTION_COUNT = 13  # wait, eight compass moves, attack, Q, W, R at visible target

def validate(payload):
    if not isinstance(payload, dict): raise ValueError("Expected object")
    seq = payload.get("seq")
    if type(seq) is not int or not 0 <= seq < 2**31: raise ValueError("Invalid sequence")
    x = np.asarray(payload.get("obs"), dtype=np.float32)
    mask = payload.get("legal")
    if x.shape != (OBS_SIZE,) or not np.isfinite(x).all() or np.max(abs(x)) > 10:
        raise ValueError("Invalid observation")
    if not isinstance(mask, list) or len(mask) != ACTION_COUNT or any(type(v) is not int or v not in (0,1) for v in mask) or mask[0] != 1:
        raise ValueError("Invalid legal mask")
    return seq, x, np.asarray(mask, dtype=bool)

class Controller:
    def __init__(self, reservoir, seed=0):
        self.reservoir = reservoir
        self.rng = np.random.default_rng(seed)
        self.decoder = self.rng.normal(0, 1, (reservoir.feature_size, ACTION_COUNT))
        self.decoder[-1] = 0  # No constant action preference independent of graph.
        self.last_seq = -1

    def step(self, payload):
        seq, obs, legal = validate(payload)
        if seq == 0: self.reservoir.reset(); self.last_seq = -1
        if seq <= self.last_seq: raise ValueError("Stale sequence")
        started = time.perf_counter()
        features = self.reservoir.features(obs)
        # Sampling is explicit engineered exploration. This readout is UNTRAINED.
        logits = features @ self.decoder * 30
        logits[~legal] = -np.inf
        p = np.exp(logits - logits.max()); p /= p.sum()
        action = int(self.rng.choice(ACTION_COUNT, p=p))
        self.last_seq = seq
        return dict(seq=seq, action=action, obs=obs.tolist(), legal=legal.astype(int).tolist(),
                    feature_norm=float(np.linalg.norm(features[:-1])),
                    decision_ms=(time.perf_counter()-started)*1000, policy="untrained-full-connectome",
                    wall_time=time.time())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log", default="work/live.jsonl")
    args = parser.parse_args()
    w, sensory, motor, manifest = load_full()
    controller = Controller(FullReservoir(w, sensory, motor, input_size=OBS_SIZE))
    logpath = Path(args.log); logpath.parent.mkdir(parents=True, exist_ok=True)
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/step": self.send_error(404); return
            try:
                n = int(self.headers.get("Content-Length", "0"))
                if not 0 < n <= 8192: raise ValueError("Invalid length")
                payload = json.loads(self.rfile.read(n))
                result = controller.step(payload)
            except (ValueError, TypeError, OverflowError):
                self.send_error(400); return
            with logpath.open("a", encoding="utf-8") as f: f.write(json.dumps(result)+"\n")
            body = f'{result["seq"]}|{result["action"]}'.encode()
            self.send_response(200); self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self, *args): pass
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    server.timeout = 2
    print(f"Ready: {manifest['selected_neurons']} neurons; localhost:{args.port}; UNTRAINED", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == "__main__": main()
