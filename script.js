// Intro tab boxes ("What is this?" / "Who am I?")
(function () {
  document.querySelectorAll('.tab-boxes').forEach(function (box) {
    var buttons = box.querySelectorAll('.tab-btn');
    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var id = btn.getAttribute('data-tab');
        buttons.forEach(function (b) {
          var on = b === btn;
          b.classList.toggle('active', on);
          b.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        box.querySelectorAll('.tab-panel').forEach(function (p) {
          p.classList.toggle('open', p.id === 'tab-panel-' + id);
        });
      });
    });
  });
})();
