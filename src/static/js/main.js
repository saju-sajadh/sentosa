(function ($) {
    "use strict";

    // // Spinner
    var spinner = function () {
        setTimeout(function () {
            if ($('#spinner').length > 0) {
                $('#spinner').removeClass('show');
            }
        }, 1);
    };
    spinner();
    
    
    // Initiate the wowjs
    new WOW().init();


    // Sticky Navbar
    $(window).scroll(function () {
        if ($(this).scrollTop() > 300) {
            $('.sticky-top').addClass('shadow-sm').css('top', '0px');
        } else {
            $('.sticky-top').removeClass('shadow-sm').css('top', '-100px');
        }
    });
    
// Back to top button
$(window).scroll(function () {
    if ($(this).scrollTop() > 300) {
        $('.back-to-top').fadeIn('slow');
    } else {
        $('.back-to-top').fadeOut('slow');
    }
});
$('.back-to-top').click(function () {
    $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
    return false;
});


// Facts counter
$('[data-toggle="counter-up"]').counterUp({
    delay: 10,
    time: 2000
});


// Roadmap carousel
$(".roadmap-carousel").owlCarousel({
    autoplay: true,
    smartSpeed: 1000,
    margin: 25,
    loop: true,
    dots: false,
    nav: true,
    navText : [
        '<i class="bi bi-chevron-left"></i>',
        '<i class="bi bi-chevron-right"></i>'
    ],
    responsive: {
        0:{
            items:1
        },
        576:{
            items:2
        },
        768:{
            items:3
        },
        992:{
            items:4
        },
        1200:{
            items:5
        }
    }
});


// Testimonials carousel
$(".testimonial-carousel").owlCarousel({
    autoplay: true,
    smartSpeed: 1000,
    margin: 25,
    loop: true,
    center: true,
    dots: false,
    nav: true,
    navText : [
        '<i class="bi bi-chevron-left"></i>',
        '<i class="bi bi-chevron-right"></i>'
    ],
    responsive: {
        0:{
            items:1
        },
        768:{
            items:2
        },
        992:{
            items:3
        }
    }
});


})(jQuery);




    let isActionModeActive = false;
    let isChatModeActive = false;
    const actionButton = document.getElementById("action-mode-button");
    const chatButton = document.getElementById("chat-mode-button");

function toggleActionMode() {
    
    const actionText = document.getElementById("action-mode-text");

    if (isActionModeActive) {
        // Send request to stop action mode
        actionText.textContent = "Surveillance Mode"; 
        isActionModeActive = false;
        chatButton.disabled = false
        fetch("/stop")
            .then(response => response.json())
            .then(data => {
                console.log(data.message);// Change text back
                isActionModeActive = false;
            })
            .catch(error=>{
                
                console.log(error)
                
            });
    } else {
        // Send request to activate action mode
        actionText.textContent = "Exit Mode"; // Change text to exit mode
        isActionModeActive = true;
        chatButton.disabled = true
        fetch("/action_mode")
            .then(response => response.json())
            .then(data => {
                console.log(data.message); 
                isActionModeActive = true;
            })
            .catch(error=>{
                
                console.log(error)
              
            });
    }
}

function toggleChatMode() {
    
    const chatText = document.getElementById("chat-mode-text");

    if (isChatModeActive) {
        // Send request to stop chat mode
        chatText.textContent = "Interaction Mode";
        isChatModeActive = false;
        actionButton.disabled = false
        fetch("/stop")
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                 // Change text back
                isChatModeActive = false;
            })
            .catch(error=>{
                
                console.log(error)
                
            })
    } else {
        // Send request to activate chat mode
        chatText.textContent = "Exit Mode"; // Change text to exit mode
        isChatModeActive = true;
        actionButton.disabled = true
        fetch("/chat_mode")
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                isChatModeActive = true;
            })
            .catch(error=>{
                ;
                console.log(error)
           
            });
    }
}


// Polling intervals (in milliseconds)
const pollInterval = 3000; // 1 second

function pollMessages() {
    if(isChatModeActive){$.ajax({
        url: '/get_messages',
        method: 'GET',
        success: function(data) {
            if (data.userMessages) {
                data.userMessages.forEach(message => {
                    addMessageToChat('You', message);
                });
            }
            if (data.botMessages) {
                data.botMessages.forEach(message => {
                    if (message.startsWith('000')) {
                        if(message.startsWith('000 HI, Unknown')){
                            let originalText= ''
                        const displayMessage = 'HI, Good to see you 👋'; // Remove "000"
                        const headingElement = document.getElementById('main-heading');
                        console.log(headingElement)
                        // Store the original text if not already stored
                        if (!originalText) {
                            originalText = headingElement.textContent;
                        }
                        // Update the heading with the new message
                        headingElement.textContent = displayMessage;
                        console.log(headingElement)
                        // Revert back to original text after 5 seconds
                        setTimeout(() => {
                            headingElement.textContent = originalText;
                            originalText = ""; // Reset original text
                        }, 25000);
                        addMessageToChat('AI', displayMessage)
                        }else{
                            let originalText= ''
                        const displayMessage = message.slice(3).trim(); // Remove "000"
                        const headingElement = document.getElementById('main-heading');
                        console.log(headingElement)
                        // Store the original text if not already stored
                        if (!originalText) {
                            originalText = headingElement.textContent;
                        }
                        // Update the heading with the new message
                        headingElement.textContent = displayMessage;
                        console.log(headingElement)
                        // Revert back to original text after 5 seconds
                        setTimeout(() => {
                            headingElement.textContent = originalText;
                            originalText = ""; // Reset original text
                        }, 25000);
                        addMessageToChat('AI', displayMessage)
                        }
                       
                    }else{
                        addMessageToChat('AI', message);
                    }
                    
                });
            }
            //scrollToBottom(); // Scroll to the bottom after appending messages
        }
    });}
}

// Function to add messages to chat
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
        // Remove the oldest message
        chatContainer.removeChild(messages[0]);
    }
}

// Start polling
setInterval(pollMessages, pollInterval);


document.getElementById('toggleChat').addEventListener('dblclick', function() {
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
