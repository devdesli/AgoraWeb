document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.like-toggle').forEach(button => {
    button.addEventListener('click', (e) => {
      e.preventDefault(); // prevent form submission or link redirect

      const icon = button.querySelector('i');

      // Toggle the icon class
      if (icon.classList.contains('bx-like')) {
        icon.classList.remove('bx-like');
        icon.classList.add('bxs-like');
      } else {
        icon.classList.remove('bxs-like');
        icon.classList.add('bx-like');
      }
    });
  });
});
