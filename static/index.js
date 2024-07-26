//使用S3Client跟S3 bucket互動，要import; 為了要放物件進S3，也要import PutObjectCommand
//安裝npm install @aws-sdk/client-s3
//dotenv 是必要的嗎? 也要import
//安裝npm install dotenv
document.addEventListener('DOMContentLoaded', function() {
    fetchOldContents()
})

document.querySelector('form').addEventListener('submit', async (event) => {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            addContent(result, true); // Pass true to indicate this is a new submission
            alert('Message and image uploaded successfully!');    
            form.reset();        
        } else {
            throw new Error('有問題，Network response was not ok');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('There was a problem with your submission.');
    }
});

let fetching = false

//抓取已經存在的內容
function fetchOldContents() {
    if (fetching) return;
    fetching = true;

    fetch('/api/contents')
    .then(response => {
        if (!response.ok) {
            throw new Error('Response from database was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log(data)
        const contentsList = document.getElementById('contents');
        data.data.forEach(content => {
            addContent(content, false); // Pass false to indicate this is existing content
        });
    })
    .catch(error => {
        console.error('Error loading existing database:', error)
    });
}

//顯示在資料庫的內容
function addContent(content, isNewContent) {
    const contentsList = document.getElementById('contents');

    const eachContent = document.createElement('div');
    const eachMessage = document.createElement('div');
    const eachImage = document.createElement('img');
    const eachSeperator = document.createElement('div');

    eachContent.className = 'each-content';
    eachMessage.textContent = content.message;
    eachMessage.className = 'each-message';
    eachImage.src = content.image_url;
    eachSeperator.className = 'seperator';
    eachImage.className = 'each-image';

    eachContent.appendChild(eachMessage);
    eachContent.appendChild(eachImage);
    eachContent.appendChild(eachSeperator);

    if (isNewContent) {
        contentsList.insertBefore(eachContent, contentsList.firstChild);
    } else {
        contentsList.appendChild(eachContent);
    }
}

