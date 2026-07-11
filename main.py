import logging
import asyncio
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
from telegram import Bot

# --- কনফিগারেশন ---
BOT_TOKEN = "8958366491:AAGX9XfEMd_4UEacUXPqyGfl8nqJlbMHejI"
CHAT_ID = "8044891553" 
SYMBOL = "EURUSD_OTC"   

# --- মার্টিনগেল সেটিংস ---
BASE_AMOUNT = 2.0         # প্রথম ট্রেডের বেস অ্যামাউন্ট (যেমন: $২)
MARTINGALE_MULTIPLIER = 2.2 # লস হলে কত গুণ বাড়বে (স্ট্যান্ডার্ড ২.২)
MAX_MARTINGALE_STEPS = 3  # সর্বোচ্চ কত ধাপ পর্যন্ত মার্টিনগেল যাবে

# গ্লোবাল ভেরিয়েবল (মার্টিনগেল ট্র্যাক করার জন্য)
current_step = 0          # বর্তমান মার্টিনগেল স্টেপ (০ মানে নরমাল ট্রেড)
current_amount = BASE_AMOUNT

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)

# ১. ওটিসি লাইভ ডাটা ফেচ করার ফাংশন
def get_otc_candles():
    try:
        url = "https://binance.com"
        response = requests.get(url).json()
        df = pd.DataFrame(response, columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        for col in ['open', 'high', 'low', 'close']:
            df[col] = df[col].astype(float)
        return df
    except Exception as e:
        logger.error(f"ডাটা ফেচ করতে সমস্যা: {e}")
        return None

# ২. ক্যান্ডেলস্টিক + ইন্ডিকেটর স্ট্র্যাটেজি ফিল্টার
def analyze_candlestick_strategy(df):
    if df is None or len(df) < 5:
        return None

    df['RSI'] = ta.rsi(df['close'], length=14)
    df['EMA_5'] = ta.ema(df['close'], length=5)
    df['EMA_20'] = ta.ema(df['close'], length=20)

    prev = df.iloc[-3]       
    current = df.iloc[-2]    
    rsi_val = current['RSI']
    
    is_bullish_trend = current['EMA_5'] > current['EMA_20']
    is_bearish_trend = current['EMA_5'] < current['EMA_20']

    # ক্যান্ডেলস্টিক প্যাটার্ন লজিক
    is_bullish_engulfing = (prev['close'] < prev['open'] and current['close'] > current['open'] and current['close'] >= prev['open'] and current['open'] <= prev['close'])
    is_bearish_engulfing = (prev['close'] > prev['open'] and current['close'] < current['open'] and current['close'] <= prev['open'] and current['open'] >= prev['close'])
    
    body_size = abs(current['close'] - current['open'])
    lower_wick = min(current['open'], current['close']) - current['low']
    is_hammer = lower_wick > (2 * body_size) and (current['high'] - max(current['open'], current['close'])) < body_size

    # সিগন্যাল ফিল্টার
    if (rsi_val < 35 or is_bullish_trend) and (is_bullish_engulfing or (is_hammer and current['close'] > current['open'])):
        return "🟢 CALL (UP)"
    elif (rsi_val > 65 or is_bearish_trend) and is_bearish_engulfing:
        return "🔴 PUT (DOWN)"

    return None

# ৩. মেইন এক্সিকিউশন লুপ
async def main_bot_loop():
    global current_step, current_amount
    
    logger.info("Finorix Martingale Bot সফলভাবে চালু হয়েছে...")
    await bot.send_message(chat_id=CHAT_ID, text="🚀 **Finorix Martingale AI Active!**\n\nUser ID: `8044891553`\nBase Trade: **${}**\nMax Steps: **MTG {}**\nআমি ১ মিনিটে মার্কেট স্ক্যান করছি।".format(BASE_AMOUNT, MAX_MARTINGALE_STEPS))

    while True:
        try:
            df = get_otc_candles()
            signal = analyze_candlestick_strategy(df)

            if signal:
                now = datetime.now()
                entry_time = now.strftime("%H:%M:00") 

                # ট্রেড টাইপ টেক্সট (নরমাল নাকি মার্টিনগেল)
                trade_type = "📊 **Fresh Entry**" if current_step == 0 else f"🔄 **MARTINGALE STEP - {current_step}**"

                message = (
                    f"🔥 **FINORIX MARTINGALE SIGNAL** 🔥\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📊 **Asset:** {SYMBOL}\n"
                    f"⏳ **Duration:** 1 MINUTE (⏱️)\n"
                    f"📈 **Action:** {signal}\n"
                    f"⏰ **Exact Entry Time:** {entry_time}\n"
                    f"💰 **Invest Amount:** **${current_amount:.2f}**\n"
                    f"🚦 **Status:** {trade_type}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"📢 *ট্রেড শেষ হওয়ার পর আপনার ফলাফল জানান (WIN/LOSS)।*"
                )
                
                # টেলিগ্রামে সিগন্যাল পাঠানো
                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
                logger.info(f"সিগন্যাল পাঠানো হয়েছে। স্টেপ: {current_step}, অ্যামাউন্ট: {current_amount}")
                
                # ট্রেড রেজাল্ট নেওয়ার জন্য ১ মিনিট অপেক্ষা (ট্রেড সম্পন্ন হওয়া পর্যন্ত)
                await asyncio.sleep(60)
                
                # সিমুলেটেড রেজাল্ট চেকার বা ইউজার ম্যানুয়াল ফিডব্যাক লজিক
                # বাস্তবে এটি ব্রোকার API থেকে অটোমেটিক উইন/লস ডাটা রিড করবে।
                # এখানে লজিক্যালি পরবর্তী পদক্ষেপ নির্ধারণ করা হচ্ছে:
                
                # ধরা যাক, আমরা পরবর্তী মেসেজের জন্য অপেক্ষা করছি বা ডিফল্ট হিসেবে টেস্ট করছি।
                # মার্টিনগেল লজিক আপডেট করার মেকানিজম:
                # if trade_lost:
                #     if current_step < MAX_MARTINGALE_STEPS:
                #         current_step += 1
                #         current_amount = current_amount * MARTINGALE_MULTIPLIER
                #     else:
                #         current_step = 0
                #         current_amount = BASE_AMOUNT
                # else: (যদি WIN হয়)
                #     current_step = 0
                #     current_amount = BASE_AMOUNT

                # সিগন্যাল জেনারেশনের পর ৮০ সেকেন্ডের সেফটি কুলডাউন ব্রেক
                await asyncio.sleep(20)
            else:
                await asyncio.sleep(10)

        except Exception as e:
            logger.error(f"লুপে ইরর: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_bot_loop())
