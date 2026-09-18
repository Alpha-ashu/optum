/**
 * Soft retry-until-200 loop.
 * Calls http_get_once.feature repeatedly until the response is HTTP 200,
 * then stops and returns immediately so the caller can move to the next request.
 * If 200 is never returned within `max` attempts it does NOT throw - it just
 * returns the last response so the caller can still save it and continue.
 *
 * arg = {
 *   max: 10,            // maximum number of attempts (default 10)
 *   interval: 3000,     // wait in ms between attempts (default 3000)
 *   req: { reqUrl, reqHeaders }   // passed straight to http_get_once.feature
 * }
 */
function (arg) {
  var max = arg.max || 10;
  var interval = arg.interval || 1000;
  var res = null;
  for (var i = 0; i < max; i++) {
    res = karate.call('classpath:utility/http_get_once.feature', arg.req);
    if (res.responseStatus == 200) {
      karate.log('Got HTTP 200 on attempt', (i + 1), '- moving on');
      break;
    }
    karate.log('Attempt', (i + 1), 'of', max, 'returned HTTP', res.responseStatus, '- retrying');
    if (i < max - 1) {
      java.lang.Thread.sleep(interval);
    }
  }
  return res;
}

