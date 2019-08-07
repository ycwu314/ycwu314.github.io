{% if theme.google_analytics.enable %}
  <script async src="" id="ga"></script>
  <script>
    var host = window.location.hostname;
    var track_id;
    if(host == 'ycwu314.gitee.io'){
      track_id = {{ theme.google_analytics.gitee_tracking_id }};  
    }else if(host == 'ycwu314.github.io'){
      track_id = {{ theme.google_analytics.github_tracking_id }};
    }

    if(track_id){
      ga.src = "https://www.googletagmanager.com/gtag/js?id=" + track_id;
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
