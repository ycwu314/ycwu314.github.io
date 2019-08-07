{% if theme.google_analytics.enable %}
  <script>
    var host = window.location.hostname;
    var track_id;
    if(host == 'ycwu314.gitee.io'){
      track_id = '{{ theme.google_analytics.gitee_tracking_id }}';  
    }else if(host == 'ycwu314.github.io'){
      track_id = '{{ theme.google_analytics.github_tracking_id }}';
    }

    if(track_id){
        var script = document.createElement("script");
        script.src = "https://www.googletagmanager.com/gtag/js?id=" + track_id;
        script.async = "async";
        document.head.appendChild(script);
    }
  </script>
  <script>
    var host = window.location.hostname;
    if (host !== "localhost" || !{{theme.google_analytics.localhost_ignored}}) {
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      if(host == 'ycwu314.gitee.io'){
        gtag('config', '{{ theme.google_analytics.gitee_tracking_id }}');  
      }else if(host == 'ycwu314.github.io'){
        gtag('config', '{{ theme.google_analytics.github_tracking_id }}');
      }
    }
  </script>
{% endif %}