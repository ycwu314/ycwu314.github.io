{% set ccLicense = theme.creative_commons.license | lower %}
{% set ccLanguage = theme.creative_commons.language %}
{% set ccIcon = '<i class="fa fa-fw fa-creative-commons"></i>' %}
{% set ccText = ccLicense | upper %}
{% if ccLicense === 'zero' %}
  {% set ccType = 'publicdomain/zero/1.0/' + ccLanguage %}
{% else %}
  {% set ccType = 'licenses/' + ccLicense + '/4.0/' + ccLanguage %}
{% endif %}
{% set ccURL = 'https://creativecommons.org/' + ccType %}

<ul class="post-copyright">
  <li class="post-copyright-author">
    <strong>{{ __('post.copyright.author') + __('symbol.colon') }} </strong>{#
  #}{{ post.author || author }}{#
#}</li>
  <li class="post-copyright-link">
    <strong>{{ __('post.copyright.link') + __('symbol.colon') }}</strong>
    {% set postURL = post.url || post.permalink %}
    {{ next_url(postURL, postURL, {title: post.title}) }}
  </li>
  <li class="post-copyright-license">
    <strong>{{ __('post.copyright.license_title') + __('symbol.colon') }} </strong>{#
  #}本博客所有文章除特别声明外，均采用 <a href="https://creativecommons.org/licenses/by-nc-nd/4.0/deed.zh" rel="external nofollow noopener noreferrer" target="_blank"><i class="fa fa-fw fa-creative-commons"></i>BY-NC-ND</a> 许可协议。未经允许请勿转载！{#
#}</li>
</ul>
