// The only JavaScript in PalShare, and it is worth being clear about why.
//
// Every other control here is a <form>, because a form works with the
// keyboard, with the back button and with scripting switched off. An emoji
// picker cannot be: inserting a character into a textarea the user is still
// typing in is not a page transition, and posting the whole form to add "🚀"
// would throw away the draft and scroll them back to the top.
//
// So it is progressive enhancement, in the strict sense: the markup ships
// hidden and this file reveals it. With JavaScript off there is no dead button
// on the page, and the textarea below still takes emoji from the system picker
// (⌃⌘Space on a Mac, Win+. on Windows) exactly as it always did.
(function () {
  "use strict";

  document.querySelectorAll("[data-emoji-picker]").forEach(function (picker) {
    var target = document.getElementById(picker.dataset.emojiPicker);
    if (!target) return;

    picker.hidden = false;

    picker.addEventListener("click", function (event) {
      var button = event.target.closest("[data-emoji]");
      if (!button) return;
      // Inside a <form>, a <button> with no type is a submit button.
      event.preventDefault();

      // Insert at the caret rather than appending, because a picker that only
      // ever appends is one that cannot put an emoji in the middle of a
      // sentence — which is where they mostly go.
      var start = target.selectionStart;
      var end = target.selectionEnd;
      var emoji = button.dataset.emoji;
      if (typeof start === "number") {
        target.value = target.value.slice(0, start) + emoji + target.value.slice(end);
        target.selectionStart = target.selectionEnd = start + emoji.length;
      } else {
        target.value += emoji;
      }
      target.focus();
    });
  });
})();
