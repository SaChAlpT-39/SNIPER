import time
from modules_utils.config_loader import ConfigLoader
from modules_utils.rate_limiter import RateLimiter

def main():
    loader = ConfigLoader('config')
    summary = loader.summarize_limits(loader.load_api_limits())

    rl = RateLimiter()
    rl.set_limit_from_summary('binance.spot', summary, burst=20)
    rl.set_limit_from_summary('binance.futures', summary, burst=40)
    rl.set_limit_from_summary('fred', summary, burst=2)

    t0 = time.time()
    # 5 appels spot coût 1
    for _ in range(5):
        rl.call('binance.spot', cost=1)
    # 3 appels futures coût 5 (endpoint weight=5)
    for _ in range(3):
        rl.call('binance.futures', cost=5)
    # 3 appels FRED coût 1
    for _ in range(3):
        rl.call('fred', cost=1)

    dt = time.time() - t0
    print(f'RateLimiter smoke OK in {dt:.2f}s')

if __name__ == '__main__':
    main()
