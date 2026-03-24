window.edgetag =
  window.edgetag ||
  function () {
    (edgetag.stubs = edgetag.stubs || []).push(arguments);
  };
edgetag('init', {
  edgeURL: 'https://ekrsz.rugiet.com',
  disableConsentCheck: true,
});
edgetag('tag', 'PageView', {}, {}, { destination: 'https://ekrsz.rugiet.com' });
