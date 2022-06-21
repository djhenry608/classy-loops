<style>
      /* CSS comes here */
      body {
          padding:20px;
          font-family: 'Avenir Next', 'Helvetica Neue', sans-serif;
          margin: 0;
      }

      input {
          padding:5px;
          background-color:transparent;
          border:none;
          border-bottom:solid 4px #8c52ff;
          width:250px;
          font-size:16px;
      }
      
      .qr-btn {
          background-color:#8c52ff;
          padding:8px;
          color:white;
          cursor:pointer;
      }

     .item {
        height: 2000px;
        padding-top: 4rem;
        padding-bottom: 4rem;
        text-align: center;
        color: #000;
      }
    </style>
    
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!--
        Required for browsers that do not yet support the latest technologies.
        http://webcomponents.org/
        https://github.com/webcomponents/webcomponentsjs/releases
        -->
        <script type="text/javascript">
        if (!document.registerElement) {
          document.writeln(decodeURI('%3Cscript%20src=%22https://cdnjs.cloudflare.com/ajax/libs/webcomponentsjs/0.7.12/webcomponents.min.js%22%20type=%22text/javascript%22%3E%3C/script%3E'));
        }
        </script>
  <script src="https://cdn.socket.io/4.4.1/socket.io.min.js" crossorigin="anonymous"></script>
  <link href="/static/css/drawer.min.css" rel="stylesheet">