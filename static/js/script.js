const text = "Hello, I’m Prem Prasad Pradhan";
let index = 0;
function typeEffect() {
  if (index < text.length) {
    document.getElementById("typewriter").innerHTML += text.charAt(index);
    index++;
    setTimeout(typeEffect, 100);
  }
}
window.onload = typeEffect;
