// 异步数据处理函数
async function postData(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    return await response.json();
}

// 处理翻译
async function handleTranslate(index) {
    const paragraph = document.querySelector(`[data-index="${index}"] p`).innerText;
    const translationDiv = document.getElementById(`translation-${index}`);

    try {
        // 显示加载状态
        translationDiv.innerHTML = '<div class="text-blue-500">Translating...</div>';
        translationDiv.classList.remove('hidden');

        // 获取当前页面URL作为来源
        const sourceUrl = window.location.href;

        // 发送请求，包含来源URL以启用词汇收集
        const response = await fetch('/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: paragraph, 
                index: index,
                source_url: sourceUrl  // 添加来源URL
            })
        });

        // 处理响应
        const result = await response.json();
        console.log('Translation API Response:', result);  // 调试日志

        if (result.error) {
            throw new Error(result.error);
        }

        if (!result.html) {
            throw new Error('Received empty translation');
        }

        // 直接使用服务器返回的HTML
        translationDiv.innerHTML = result.html;

        // 显示词汇收集成功提示（可选）
        if (result.translation && result.translation.vocabulary && result.translation.vocabulary.length > 0) {
            console.log(`已收集 ${result.translation.vocabulary.length} 个词汇到个人词汇库`);
        }

    } catch (error) {
        console.error('Translation Failed:', error);
        translationDiv.innerHTML = `
            <div class="text-red-500">
                Translation Error: ${error.message}
            </div>
        `;
    }
}

// 修改后的TTS处理函数
async function handleTTS(index, event) {  // 添加event参数
    const button = event.currentTarget  // 直接获取触发按钮
    const paragraph = document.querySelector(`[data-index="${index}"] p`).innerText

    try {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'
        button.disabled = true

        const response = await postData('/tts', {
            text: paragraph,
            index: index
        })

        if (response.success) {
            const audio = new Audio(response.audio_url)
            audio.play().catch(error => {
                console.error('播放失败:', error)
                button.innerHTML = '<i class="fas fa-volume-up fa-sm"></i>'
            })
        }
    } catch (error) {
        console.error('请求失败:', error)
    } finally {
        button.innerHTML = '<i class="fas fa-volume-up fa-sm"></i>'
        button.disabled = false
    }
} 