function jump(host) {
    const question = document.getElementById("question").value;
    if (host === "baidu") {
        window.location.href = "https://www.baidu.com/s?wd=" + question
    } else if (host === "bing") {
        window.location.href = "https://cn.bing.com/search?q=" + question
    } else if (host === "google") {
        window.location.href = "https://www.google.com/search?q=" + question
    }
}
