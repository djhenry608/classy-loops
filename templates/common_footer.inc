<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.2.4/jquery.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/iScroll/5.2.0/iscroll.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/js/bootstrap.min.js"></script>
  <!-- Bootstrap dropdown v4.0.0-alpha -->
  <!-- <script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.0.0-alpha/js/bootstrap.min.js"></script> -->
  <script src="/static/js/drawer.min.js" charset="utf-8"></script>
  <script>
    $(document).ready(function() {
      $('.drawer').drawer();
    });

    // initialize variables
    var socket = io.connect('http://{{ myIP }}:8080');
    //var socket = io.connect('http://localhost:8080');
    //sending data from the user via a socket.io
    socket.on("test", function (data) {
      data.forEach(obj => {
        console.log("Yer : " + obj.yer + ", Lat : " + obj.lat + ", Long : " + obj.lng);
      })
    });

    function saveProfile() {
     var profile = {'name': 'unknown','samples':[]};
     profile['name'] = document.getElementById('profileName').value;
     sampleFiles = document.getElementById('sampleFiles');
     var samples = [];
     for (var option of sampleFiles.options)
     {
        if (option.selected) {
            samples.push(option.value);
        }
     }
     profile['samples'] = samples;
     socket.emit('saveProfile', JSON.stringify(profile));
    }

    function loadProfile() {
      var e = document.getElementById("profileList");
      var profileID = e.value;
      console.log('ProfileID: ',profileID);
      socket.emit('loadProfile', JSON.stringify(profileID));
    }

  </script>