
const chatButton = document.getElementById("chat-mode-button");
let powerOn = false;
const pollInterval = 3000;

const carouselItems = document.querySelectorAll(".carousel_item");
let i = 1;


setInterval(() => {
  Array.from(carouselItems).forEach((item, index) => {

    if (i < carouselItems.length) {
      item.style.transform = `translateX(-${i * 100}%)`
    }
  })
  if (i < carouselItems.length) {
    i++;
  }
  else {
    i = 0;
  }
}, 2000)

function toggleChatMode() {
  if(!powerOn){
    fetch("/activate")
    .then(response => response.json())
    .then(data => {
      console.log(data.message);
      powerOn = true;
    })
    .catch(error => {
      console.log(error)
      powerOn = false
    });
  }else{
    fetch("/stop")
    .then(response => response.json())
    .then(data => {
      console.log(data.message);
      powerOn = false
    })
    .catch(error => {
      console.log(error)
      powerOn = true
    });
  }
}


function pollMessages() {
  if (powerOn) {
    fetch("/get_messages", {
      method: "GET",
    })
      .then(response => response.json())
      .then(data => {
        console.log(data)
        if (data.userMessages) {
          data.userMessages.forEach(message => {
            addMessageToChat('You', message);
          });
        }
        if (data.botMessages) {
          data.botMessages.forEach(message => {
            if (message.startsWith('000')) {
              if (message.startsWith('000 HI, Unknown')) {
                let originalText = ''
                const displayMessage = 'HI, Good to see you 👋'; // Remove "000"
                const headingElement = document.getElementById('main-heading');
                // Store the original text if not already stored
                if (!originalText) {
                  originalText = headingElement.textContent;
                }
                // Update the heading with the new message
                headingElement.textContent = displayMessage;
                // Revert back to original text after 5 seconds
                setTimeout(() => {
                  headingElement.textContent = 'Hello 👋, I am Sentosa';
                  originalText = ""; // Reset original text
                }, 25000);
                addMessageToChat('AI', displayMessage)
              } else {
                console.log('entered')
                let originalText = ''
                const displayMessage = message.slice(3).trim(); // Remove "000"
                const headingElement = document.getElementById('main-heading');
                // Store the original text if not already stored
                if (!originalText) {
                  originalText = headingElement.textContent;
                }
                // Update the heading with the new message
                headingElement.textContent = displayMessage;
                // Revert back to original text after 5 seconds
                setTimeout(() => {
                  headingElement.textContent = 'Hello 👋, I am Sentosa';
                  originalText = ""; // Reset original text
                }, 25000);
                addMessageToChat('AI', displayMessage)
              }

            } else {
              addMessageToChat('AI', message);
            }
            if (message.startsWith('111')) {
              const imgs = {
                library: ['/static/img/library1.jpg', '/static/img/library2.jpg'],
                Play: ['/static/img/playarea.jpg'],
                laboratory: ['/static/img/laboratory1.jpg', '/static/img/laboratory2.jpg'],
                seminar: ['/static/img/seminarhall1.jpg', '/static/img/seminarhall2.jpg'],
                auditorium: ['/static/img/auditorium.jpg']
              };
              const mapDiv = document.getElementById('map');
              const imagesDiv = document.getElementById('images');
              for (const key in imgs) {
                if (message.includes(key)) {
                  imagesDiv.style.display = 'none';
                  mapDiv.style.display = 'grid';
                  mapDiv.innerHTML = '';
                  imgs[key].forEach(imageUrl => {
                    const imgElement = document.createElement('img');
                    imgElement.src = imageUrl;
                    imgElement.style.width = '100%';
                    imgElement.style.height = 'auto';
                    imgElement.style.display = 'block';
                    mapDiv.appendChild(imgElement);
                  });
                  setTimeout(() => {
                    mapDiv.style.display = 'none';
                    imagesDiv.style.display = 'block';
                    mapDiv.innerHTML = '';
                  }, 10000);
                  break;
                }
              }
            }
          });
        }
      }
      )
  }
}



function addMessageToChat(speaker, message) {
  const chatContainer = document.getElementById('chat-messages');
  const messageHTML = `
        <div id="chat" class="flex gap-3 my-4 text-gray-600 text-sm flex-1">
            <span class="relative flex shrink-0 overflow-hidden rounded-full w-8 h-8">
                <div class="rounded-full bg-gray-100 border p-1">
                    <!-- SVG Icon -->
                </div>
            </span>
            <p class="leading-relaxed"><span class="block font-bold text-gray-700">${speaker}</span> ${message}</p>
        </div>
    `;
  chatContainer.innerHTML += messageHTML;
  const messages = chatContainer.getElementsByClassName('flex');
  if (messages.length > 6) {
    chatContainer.removeChild(messages[0]);
  }
}


setInterval(pollMessages, pollInterval);


document.getElementById('toggleChat').addEventListener('dblclick', function () {
  const fullscreenContainer = document.getElementById(
    "fullscreen-container"
  );
  if (document.fullscreenEnabled) {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      fullscreenContainer.requestFullscreen();
    }
  } else {
    console.log("Full screen mode is not supported by this browser.");
  }
});

function moveEye(x, y) {
  const eyeImage = document.querySelector('img[src*="eyes.gif"]');
  const section = document.getElementById('sec');
  const centerX = section.offsetWidth / 2;
  const centerY = section.offsetHeight / 2;

  let newX;
  if (x === 300 || x === 0) {
    newX = centerX;
  } else if (x < 300 && x !== 0 && x < 380) {
    newX = centerX - ((300 - x) / 300) * (section.offsetWidth / 2);
  } else if(x > 300) {
    newX = centerX + ((x - 300) / 300) * (section.offsetWidth / 2);
  }

  eyeImage.style.transition = 'transform 0.5s ease'; 
  eyeImage.style.transform = `translateX(${newX - centerX}px)`;

}

function updateEyePosition() {
  fetch('/get_position')
    .then(response => response.json())
    .then(data => {
      const { x, y } = data;
      console.log(data)
      if (x != null && y != null) {
        moveEye(x, y);
      }
    })
    .catch(error => console.error('Error fetching position:', error));
}




setInterval(updateEyePosition, 100);

function toggleChat() {
  const chatContainer = document.getElementById('chat-container');
  if (chatContainer.style.display === 'none' || chatContainer.style.display === '') {
    chatContainer.style.display = 'block';
  } else {
    chatContainer.style.display = 'none';
  }
}


const fullscreenBtn = document.getElementById("fullscreen-btn");
const fullscreenContainer = document.getElementById(
  "fullscreen-container"
);
fullscreenBtn.addEventListener("click", toggleFullScreen);
function toggleFullScreen() {
  if (document.fullscreenEnabled) {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      fullscreenContainer.requestFullscreen();
    }
  } else {
    console.log("Full screen mode is not supported by this browser.");
  }
}

let eventSource;

function startListening() {
  eventSource = new EventSource('/listen_status');
  eventSource.onmessage = function (event) {
    const listeningStatus = event.data;
    const listeningElement = document.getElementById("listening");
    if (listeningStatus === 'listening' && powerOn) {
      listeningElement.classList.remove("hidden"); 
    } else {
      listeningElement.classList.add("hidden");
    }
  };
  eventSource.onerror = function () {
    console.error("Error occurred in SSE connection.");
    document.getElementById("listening").classList.add("hidden");
    eventSource.close();  
  };
}
window.onbeforeunload = function () {
  if (eventSource) {
    eventSource.close();  
    console.log("SSE connection closed.");
  }
};
window.onload = function () {
  startListening(); 
};

//#3E2863 #D9418D #FFE250