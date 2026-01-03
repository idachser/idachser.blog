document.addEventListener("DOMContentLoaded", function () {
  const lightbox = document.getElementById("lightbox");
  const lightboxImg = document.getElementById("lightbox-img");
  const closeBtn = document.querySelector(".close");
  const thumbnails = document.querySelectorAll(".media");

  if (!lightbox || !lightboxImg) return;

  thumbnails.forEach((img) => {
    img.addEventListener("click", () => {
      lightboxImg.src = img.src;
      lightbox.style.display = "flex";
    });
  });

  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox || event.target === closeBtn) {
      lightbox.style.display = "none";
    }
  });
});
