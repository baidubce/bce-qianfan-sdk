import {ChatCompletion} from '../ChatCompletion';


const API_KEY = 'GwN3oQ2vvWKowHyvB4FONI9T';
const SECRET_KEY = 'UUAXXbbwxKl456f6fMB4hfnfCmrI7hdv';
const client = new ChatCompletion(API_KEY, SECRET_KEY);

async function main() {
    const resp = await client.baseChat({
        messages: [
            {
                role: 'user',
                content: '你好，请问你是哪个模型？',
            },
        ],
    }, 'Yi-34B-Chat');
    console.log(resp);

    // const text2image_resp = await client.text2image({
    //     prompt: "cat",
    // });
    // console.log(text2image_resp);
}

main();