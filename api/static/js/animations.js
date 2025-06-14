
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.question-card');
  cards.forEach(card => {
    card.classList.add('animate-fade-in-up');
  });
});
