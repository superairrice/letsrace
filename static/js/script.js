
// Menu
const dropdownMenu = document.querySelector(".dropdown-menu");
const dropdownButton = document.querySelector(".dropdown-button");

if (dropdownButton) {
  dropdownButton.addEventListener("click", () => {
    dropdownMenu.classList.toggle("show");
  });
}


// Upload Image
const photoInput = document.querySelector("#avatar");
const photoPreview = document.querySelector("#preview-avatar");
if (photoInput)
  photoInput.onchange = () => {
    const [file] = photoInput.files;
    if (file) {
      photoPreview.src = URL.createObjectURL(file);
    }
  };

// Scroll to Bottom
const conversationThread = document.querySelector(".room__box");
if (conversationThread) conversationThread.scrollTop = conversationThread.scrollHeight;


window.setTimeout(function() {
    $(".alert-auto-dismissible").fadeTo(500, 0).slideUp(500, function(){
        $(this).remove();
    });
}, 4000);

window.onpageshow = function (event) {

    // 새로고침: window.performance.navigation.type == 1
    // 뒤로가기: window.performance.navigation.type == 2
    if (event.persisted || (window.performance && (window.performance.navigation.type == 1 || window.performance.navigation.type == 2))) {
    
        // 현재 브라우저에서 WebStorage를 지원할 때
        if (('sessionStorage' in window) && window['sessionStorage'] !== null) {
        
            // sessionStorage로 데이터 다시 불러오기
            if (sessionStorage.getItem('DATA')) {
                input_text.value = sessionStorage.getItem('DATA');
            }
            
        }
        
    }
    
}

function popupCenter(href, w, h) {
	var xPos = (document.body.offsetWidth/2) - (w/2); // 가운데 정렬
	xPos += window.screenLeft; // 듀얼 모니터일 때
	var yPos = (document.body.offsetHeight/2) - (h/2);

	window.open(href, "pop_name", "width="+w+", height="+h+", left="+xPos+", top="+yPos+", menubar=yes, status=yes, titlebar=yes, resizable=yes");
}

function openCenteredPopup(url, name, width, height) {
    // 현재 화면의 너비와 높이 가져오기
    const screenWidth = window.innerWidth || document.documentElement.clientWidth || screen.width;
    const screenHeight = window.innerHeight || document.documentElement.clientHeight || screen.height;

    // 팝업을 중앙에 배치하기 위한 좌표 계산
    const left = (screenWidth - width) / 2;
    const top = (screenHeight - height) / 2;

    // 팝업 창 열기
    window.open(url, name, `width=${width}, height=${height}, top=${top}, left=${left}, resizable=yes, scrollbars=yes`);
}

function openCenteredWindow(url, name, width, height) {
  // 현재 화면 크기 가져오기
  const screenWidth = window.screen.width;
  const screenHeight = window.screen.height;

  // 팝업을 중앙에 배치하기 위한 좌표 계산
  const left = (screenWidth - width) / 2;
  const top = (screenHeight - height) / 2;

  // 새 창 열기
  window.open(
    url,
    name,
    `width=${width}, height=${height}, top=${top}, left=${left}, resizable=yes, scrollbars=yes`
  );
}