# XAUUSD AI — Plan A (100% free)

Phone (iPhone) + PC off. Signals from free Yahoo/Gold-API data. Educational only.

## Run locally
```
pip install -r requirements.txt
python -m src.data_fetch
python -m src.train
python -m src.backtest
python -m src.signal
streamlit run app.py
```

## Telegram setup (free push to iPhone)
1. Message @BotFather on Telegram → /newbot → copy token.
2. Message your bot once, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` to get `chat.id`.
3. Local test:
```
set TELEGRAM_BOT_TOKEN=xxx
set TELEGRAM_CHAT_ID=yyy
python check_signal.py
```

## Deploy free (PC can stay off)
1. Push this folder to GitHub.
2. Go to share.streamlit.io → New app → select repo, `app.py`.
3. In app Settings → Secrets add:
```
TELEGRAM_BOT_TOKEN="xxx"
TELEGRAM_CHAT_ID="yyy"
```
4. On iPhone Safari open the streamlit URL → Share → Add to Home Screen.
5. Schedule `check_signal.py` hourly: easiest free = GitHub Actions cron (runs even when PC off).

## Honest results (2026-10-14 run)
- H1 rows: 5708, train samples: 3775
- Test accuracy: 52% (SELL f1 0.61 / BUY f1 0.37)
- Backtest (hold 4H, spread 0.02%): 554 trades, winrate 48.2%, total -3.13%
- Meaning: v1 has NO edge yet. Do NOT trade live. Next: raise threshold to 0.70, add DXY filter, news filter.
