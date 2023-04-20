
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



/////////////////////////////////////////////////
//userAgent를 받아서 클라이언트 정보를 출력하는 함수입니다.
function identifyBrowser(userAgent) {
    
    //파라메타가 주어지지 않을 경우 현재 위치의 userAgent를 이용
    if(userAgent === undefined) {
        userAgent = navigator.userAgent;
    }

    //결과를 출력할 객체를 선언합니다.
    let result = new Object();
    
    result.userAgent = userAgent;
    result.width = screen.width;
    result.height = screen.height;
    result.language = navigator.language;
    result.referer = document.referrer;
    result.pathname = location.pathname;
    result.time = new Date();


    //-----------------------브라우저 검증---------------------------    
    
    //1. IE 10 이하 검증
    if(/MSIE/.test(userAgent)){
        result.browser = userAgent.match(/IE \d+.\d+/);
    }

    //2. IE11 검증
    else if(/Trident/.test(userAgent)) {
        result.browser = "IE " + userAgent.match(/rv:\d+\.\d+/)[0].replace("rv:", "");
    }

    //3. Firefox 검증
    else if(/Firefox/.test(userAgent)) {
        result.browser = userAgent.match(/Firefox\/\d+\.\d+/)[0].replace("/", " ");
    }

    //4. Opera Touch 검증
    else if(/OPT/.test(userAgent)) {
        result.browser = userAgent.match(/OPT\/\d+\.?[0-9]?/)[0].replace("/", " ").replace("OPT", "Opera Touch");
    }

    //5. Opera Mini 검증
    else if(/Opera Mini/.test(userAgent)) {
        result.browser = userAgent.match(/Opera Mini\/\d+\.\d+/)[0].replace("/", " ");
    }

    //6. Opera 검증
    else if(/OPR/.test(userAgent) || /Opera/.test(userAgent)) {
        if(/OPR/.test(userAgent)) {
             result.browser = "Opera" + userAgent.match(/OPR\/\d+\.\d+/)[0].replace("OPR/", " ");
        }else if(/Opera\//) {
            result.browser = "Opera" + userAgent.match(/Version\/\d+\.\d+/)[0].replace("Version/", " ");
        }else {
            result.browser = userAgent.match(/Opera \d+\.\d+/)[0];
        }
    }

    //7.Edge 검증
    else if(/Edg/.test(userAgent)) {
        result.browser = userAgent.match(/Edg[e]*\/\d+\.\d+/)[0].replace("/", " ").replace("Edge", "Edg").replace("Edg", "Edge");
    }
    
    //8. SamsungBrowser 검증
    else if(/SamsungBrowser/.test(userAgent)) {
        result.browser = userAgent.match(/SamsungBrowser\/\d+\.\d+/)[0].replace("/", " ");
    }

    //9. Whale 검증
    else if(/Whale/.test(userAgent)) {
        result.browser = userAgent.match(/Whale\/\d+\.\d+/)[0].replace("/", " ");
    }

    //10. Safari 검증
    else if(/Safari/.test(userAgent) && !/Chrome/.test(userAgent)) {
        result.browser = "Safari " + userAgent.match(/Version\/\d+\.[0-9]/)[0].replace("Version/", "");
    }

    //11. Chrome 검증
    else if(/Chrome/.test(userAgent)) {
        result.browser = userAgent.match(/Chrome\/\d+\.\d+/)[0].replace("/", " ");
    }

    //12. 기타
    else {
        result.browser = "unknown";
    }

    //----------------------------OS 검증-----------------------------

    //1. Windows 검증
    if(/Windows/.test(userAgent)) {
        result.os = "Windows ";
        let osv = userAgent.substring(userAgent.indexOf("Windows NT ")+11, userAgent.indexOf("Windows NT ")+15);
        if(/5.0/.test(osv)) result.os += "2000";
        else if(/5.1/.test(osv)) result.os += "XP";
        else if(/5.2/.test(osv)) result.os += "XP";
        else if(/6.0/.test(osv)) result.os += "Vista";
        else if(/6.1/.test(osv)) result.os += "7";
        else if(/6.2/.test(osv)) result.os += "8";
        else if(/6.3/.test(osv)) result.os += "8.1";
        else if(/10.0/.test(osv)) result.os += "10";
        else result.os += "unknown";
    }

    //2. Android 검증
    else if(/Android/.test(userAgent)) {
        if(userAgent.match(/Android \d+\.?\d?\.?\d?/)) {
            result.os = userAgent.match(/Android \d+\.?\d?\.?\d?/);
        }else {
            result.os = "Android unknown ver.";
        }
    }
            
    //3. iPhone 검증
    else if(/iPhone/.test(userAgent)) {
        result.os = "iPhone";
        if(/iPhone OS/.test(userAgent)) {
            result.os = userAgent.match(/iPhone OS \d+_\d+_?[0-9]?/)[0].replace(" OS", "").replaceAll("_", ".");
        }else if(/iPhone/.test(userAgent)) {
            result.os = "iPhone unknown ver.";
        }
    }

    //4. iPad 검증
    else if(/iPad/.test(userAgent)) {
        result.os = "iPad " + userAgent.match(/CPU OS \d+_\d+_?[0-9]?/)[0].replace("CPU OS ", "").replaceAll("_", ".");
    }

    //5. Mac 검증
    else if(/Mac OS X/.test(userAgent)) {
        result.os = userAgent.match(/Mac OS X \d+_\d+_?[0-9]?/)[0].replace(" OS X", "").replaceAll("_", ".");
    }    

    //6. 리눅스 검증
    else if(/Linux/.test(userAgent)) {
        result.os = "Linux";
        if(/Ubuntu/.test(userAgent)) {
            result.os += " Ubuntu";
        }
    }

    //7. 기타
    else {
        result.os = "unknown";
    }

    alert(`browser : ${result.browser}\n`+
         `os : ${result.os}\n`+
         `screen : ${result.width} X ${result.height}\n`+
         `language : ${result.language}\n`+
         `referer : ${result.referer}\n`+
         `pathname : ${result.pathname}\n`+
         `time : ${result.time}`)
    return result;
}