"""Local Workshop transport. Untrained full-connectome smoke policy, not Dota AI."""
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import numpy as np
from .malecns import load_full
from .full_neural import FullReservoir
from .reinforcement import RewardLearner

OBS_SIZE = 33
ACTION_COUNT = 25  # combat 0..13; upgrade 14..17; buy 18..24

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
    def __init__(self, reservoir, seed=0, policy=None, learn=False):
        self.reservoir = reservoir
        self.rng = np.random.default_rng(seed)
        self.decoder = self.rng.normal(0, 1, (reservoir.feature_size, ACTION_COUNT))
        self.decoder[-1] = 0  # No constant action preference independent of graph.
        self.last_seq = -1
        self.latest = None
        self.self_fields=None
        self.policy_name='full-observation-RL-from-scratch' if learn else 'untrained-full-connectome'
        self.learner=RewardLearner(reservoir.feature_size,ACTION_COUNT) if learn else None
        if policy:
            with np.load(policy,allow_pickle=False) as data:
                if int(data['input_size'])!=OBS_SIZE or int(data['action_count'])!=ACTION_COUNT:raise ValueError('Checkpoint schema mismatch')
                self.decoder=data['decoder'].copy();self.self_fields=data['self_fields'].astype(int)
                if self.decoder.shape!=(reservoir.feature_size,ACTION_COUNT) or not np.isfinite(self.decoder).all():raise ValueError('Invalid decoder')
                if not np.array_equal(self.self_fields,[0,1,2,3,4]):raise ValueError('Unexpected input selection')
            self.policy_name='pro-SF-own-state-imitation'

    def step(self, payload):
        seq, obs, legal = validate(payload)
        reward=payload.get('reward',0)
        assisted=payload.get('assisted',False)
        if type(assisted) is not bool or assisted:raise ValueError('Script-assisted sessions are disabled')
        if type(reward) not in (int,float) or not np.isfinite(reward) or abs(reward)>20:raise ValueError('Invalid reward')
        if seq == 0:
            self.reservoir.reset(); self.last_seq = -1
            if self.learner:self.learner.reset_episode()
        if seq <= self.last_seq: raise ValueError("Stale sequence")
        if self.learner:self.learner.feedback(reward)
        started = time.perf_counter()
        neural_obs=obs.copy()
        if self.self_fields is not None:
            neural_obs[:]=0;neural_obs[self.self_fields]=obs[self.self_fields]
        features = self.reservoir.features(neural_obs)
        # Sampling is explicit engineered exploration. This readout is UNTRAINED.
        logits = features @ self.decoder * (30 if self.self_fields is None else 1)
        if self.learner:logits += self.learner.logits(features)
        logits[~legal] = -np.inf
        p = np.exp(logits - logits.max()); p /= p.sum()
        action = int(self.rng.choice(ACTION_COUNT, p=p)) if self.self_fields is None or self.learner else int(np.argmax(logits))
        if self.learner:self.learner.record(features,p,action)
        self.last_seq = seq
        result = dict(seq=seq, action=action, obs=obs.tolist(), legal=legal.astype(int).tolist(),
                    feature_norm=float(np.linalg.norm(features[:-1])),
                    decision_ms=(time.perf_counter()-started)*1000, policy=self.policy_name,
                    wall_time=time.time(),reward=reward,
                    total_reward=self.learner.total_reward if self.learner else 0,
                    learning_updates=self.learner.updates if self.learner else 0,
                    learning='reward-modulated engineered readout' if self.learner else 'disabled')
        result['assisted']=assisted
        result['control_mode']='SCRIPT-ASSISTED: route, attack-move, retreat, shop, levels' if assisted else 'neural actions with legality mask'
        sample=np.linspace(0,self.reservoir.n-1,min(240,self.reservoir.n),dtype=int)
        self.latest=dict(**result, neurons=self.reservoir.n,
                         sampled_indices=sample.tolist(),activity=self.reservoir.state[sample].tolist(),
                         motor_pools=features[:-1].tolist(),probabilities=p.tolist())
        return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--log", default="work/live.jsonl")
    parser.add_argument('--policy',help='Full-model SF readout checkpoint')
    parser.add_argument('--learn',action='store_true',help='Experimental online reward-modulated readout updates')
    parser.add_argument('--resume-learning',help='Resume an experimental readout adapter checkpoint')
    args = parser.parse_args()
    w, sensory, motor, manifest = load_full()
    controller = Controller(FullReservoir(w, sensory, motor, input_size=OBS_SIZE),policy=args.policy,learn=args.learn)
    if args.resume_learning:
        if not controller.learner:raise ValueError('--resume-learning requires --learn')
        with np.load(args.resume_learning,allow_pickle=False) as saved:
            weights=saved['weights']
            if weights.shape!=controller.learner.weights.shape or not np.isfinite(weights).all():raise ValueError('Invalid learning checkpoint')
            controller.learner.weights[:]=weights
            controller.learner.total_reward=float(saved['total_reward'])
            controller.learner.updates=int(saved['updates'])
    logpath = Path(args.log); logpath.parent.mkdir(parents=True, exist_ok=True)
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/state':
                body=json.dumps(controller.latest or dict(status='Waiting for real Dota observations')).encode()
                mime='application/json'
            elif self.path == '/':
                body=Path(__file__).with_name('dashboard.html').read_bytes(); mime='text/html; charset=utf-8'
            else: self.send_error(404); return
            self.send_response(200); self.send_header('Content-Type',mime)
            self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(body)))
            self.end_headers(); self.wfile.write(body)
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
            if controller.learner and result['seq']%25==0:
                np.savez_compressed(logpath.with_suffix('.learning.npz'),weights=controller.learner.weights,
                                    total_reward=controller.learner.total_reward,updates=controller.learner.updates)
            body = f'{result["seq"]}|{result["action"]}'.encode()
            self.send_response(200); self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self, *args): pass
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    server.timeout = 2
    print(f"Ready: {manifest['selected_neurons']} neurons; localhost:{args.port}; {controller.policy_name}", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally:
        server.server_close()
        if controller.learner:
            np.savez_compressed(logpath.with_suffix('.learning.npz'),weights=controller.learner.weights,
                                total_reward=controller.learner.total_reward,updates=controller.learner.updates)

if __name__ == "__main__": main()
