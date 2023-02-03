window.dash_clientside = Object.assign({}, window.dash_clientside, {
  cx: {
    pollQueue: function (nClicks) {
      return fetch('/celery-queue', {
        // method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json'
        }
        // body: JSON.stringify({ nClicks })
      }).then(res => res.text())
    }
  }
})
