import procError from './procError'
import config from '../../config.json' assert { type: 'json' }

import { sendMessage, sendPhoto, sendChatAction } from '../helper/telegram'
import { MessageNameNotFoundError } from '../error'

import {
  getChartImgQuery,
  getQueryByCmdText,
  getChartImgPhoto,
  getInitChartInlineKeys,
} from '../helper/query'

/**
 * @param {Chat} chat message
 * @param {String} text command eg. /chart binance:btcusdt, /nasdaq, /crypto, /crypto@yourBot
 * @param {Env} env
 * @returns {Promise}
 */
export default async function (chat, text, env) {
  const { TELEGRAM_API_TOKEN, CHART_IMG_API_KEY } = env

  try {
    const cmdKey = text.split(' ')[0].split('@')[0]

    if (config[cmdKey]) {
      const textQuery = config[cmdKey].inputs
        ? getQueryByCmdText(cmdKey) // preset exist
        : getQueryByCmdText(text.split('@')[0])

      const chartQuery = getChartImgQuery(cmdKey, textQuery)

      const [chartPhoto] = await Promise.all([
        getChartImgPhoto(CHART_IMG_API_KEY, chartQuery),
        sendChatAction(TELEGRAM_API_TOKEN, chat), // action >>> sending a photo
      ])

      return sendChartPhoto(
        TELEGRAM_API_TOKEN,
        chat,
        chartPhoto,
        cmdKey,
        textQuery
      )
    } else {
      return sendMessageByName(TELEGRAM_API_TOKEN, chat, text)
    }
  } catch (error) {
    return procError(error, chat, env)
  }
}

/**
 * @param {String} apiToken
 * @param {Chat} chat
 * @param {Blob} photo
 * @param {String} cmdKey
 * @param {Object} query
 * @returns {Promise}
 */
function isEmpty(obj) {
  for (const prop in obj) {
    if (Object.hasOwn(obj, prop)) {
      return false;
    }
  }

  return true;
}
async function getCsvContent( symbol ) {
  try {
	  
    const response = await fetch('http://localhost/broadcast.csv');
    const text = await response.text();
    const csvData = text;
    const datarows = csvData.split('\n');
    const rows = datarows.slice(1);
    const object = {};
    for (const row of rows) {
      const cells = row.split(',');
      if(isEmpty(cells[0])){ continue; }
      if (symbol.toUpperCase() == 'NSE:'+cells[0].toUpperCase() ){
	let  message = `📈 Stock name: ${cells[1]} (${cells[0]})\n\n` +
                                `️🎚️ Volume: ${cells[3]}\n\n` +
                                `💹 Current Price: ₹${cells[4]}\n\n` +
                                `⭐ Finstar Rating: ${cells[5]}\n\n` +
                                `️🎖️ Valuation Rating: ${cells[6]}`;
        let nsecode = cells[0]
        let price = cells[4]
        let currentDate = new Date();
        let isoDateString = currentDate.toISOString();
        const jsonBody = {
            "nsecode": nsecode,
            "price": price,
            "date" : isoDateString,
        };
        return [message, jsonBody];
      }	    
    }	
  } catch (error) {
    console.error('Error fetching file:', error);
    return  " "	  
  }
}

async function sendChartPhoto(apiToken, chat, photo, cmdKey, query = {}) {
  const { symbol, interval } = query

  if (symbol && interval) {
    // send photo without reply markup inline keyboad
	  const [csvContent, jsonBody] = await getCsvContent(symbol);  
    const response = await sendPhoto(apiToken, chat, photo, {
      caption: `${csvContent}`
    })
    let response_data = await response.json()
    let messageId = response_data.result.message_id
    const apiRecommendUrl = 'http://127.0.0.1:5000/update/recommendation';
    jsonBody["message_id"] = messageId
    const apiRecommendresponse = await fetch(apiRecommendUrl, {
      method: 'POST', 
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(jsonBody)
    });
    const apiRecommendresponseData = await apiRecommendresponse.json();

    return response
  } else {
    const cmdKeyDefault = config[cmdKey].default
    const opt = {
      caption: `${symbol || cmdKeyDefault.symbol} ${interval || cmdKeyDefault.interval}`, // prettier-ignore
      reply_markup: JSON.stringify({
        inline_keyboard: getInitChartInlineKeys(cmdKey, query, !symbol),
      }),
    }

    return sendPhoto(apiToken, chat, photo, opt) // send photo with inline keyboard
  }
}

/**
 * @param {String} apiToken
 * @param {Chat} chat
 * @param {String} name
 * @returns {Promise}
 */
function sendMessageByName(apiToken, chat, name) {
  const message = getMessage(name.split('@')[0])

  if (message?.text) {
    const payload = {
      chat_id: chat.id,
      text: message.text,
    }

    if (message.parseMode) {
      payload.parse_mode = message.parseMode
    }

    return sendMessage(apiToken, payload)
  } else {
    throw new MessageNameNotFoundError(name)
  }
}

/**
 * @param {String} name
 * @returns {Object|undefined}
 */
function getMessage(name) {
  return config.messages.find((message) => message.name === name)
}
