document.getElementById("main").classList.add('loading');
window.addEventListener("load", function () {
  document.getElementById("main").classList.remove('loading');
  {{ should_print }}
});
// Mobile download button animation
var prevYOffset = window.pageYOffset;
window.onscroll = function () {
  var button = document.getElementById("dl-small");
  if (window.pageYOffset == 0 || prevYOffset - 20 > window.pageYOffset) {
    button.style.visibility = "visible";
    button.style.opacity = 1;
    button.style.bottom = "2.5%"
  } else if (prevYOffset < window.pageYOffset) {
    button.style.visibility = "hidden";
    button.style.opacity = 0;
    button.style.bottom = "5%"
  }
  prevYOffset = window.pageYOffset;
};