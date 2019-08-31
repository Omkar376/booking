$.ajax({
  url: "https://api.apiscience.com/v1/monitors/1572022",
  headers: {
    "Authorization" : "Bearer NN_6xxxxx"
  }
}).done(function(data) {
  $('#monitor_data').append(JSON.stringify(data))
});