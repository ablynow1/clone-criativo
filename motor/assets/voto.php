<?php
// Votos e ajustes dos lotes de criativos (Clone Criativo).
// POST {"votos":[{"id","v","c","t"}]} grava no fim de dados/votos.jsonl
//   v: 1 aprovado · -1 reprovado · 0 desfeito · 2 só comentário (não mexe no voto)
// GET ?estado=1 devolve, por id, o último voto e o último comentário: {"ok":true,"votos":{"<id>":[v,t,"comentário"]}}
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex, nofollow');

$dir = __DIR__ . '/dados';
$log = $dir . '/votos.jsonl';
$ids = json_decode((string) @file_get_contents(__DIR__ . '/ids.json'), true);
$valido = is_array($ids) ? array_flip(array_map('strval', $ids)) : array();

function sai($cod, $dados) { http_response_code($cod); echo json_encode($dados, JSON_UNESCAPED_UNICODE); exit; }

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $bruto = (string) file_get_contents('php://input', false, null, 0, 200000);
    $in = json_decode($bruto, true);
    if (!is_array($in)) sai(400, array('ok' => false, 'erro' => 'json'));
    $lote = (isset($in['votos']) && is_array($in['votos'])) ? $in['votos'] : array($in);
    if (count($lote) > 200) sai(413, array('ok' => false, 'erro' => 'lote grande'));
    if (is_file($log) && filesize($log) > 8 * 1024 * 1024) sai(507, array('ok' => false, 'erro' => 'arquivo cheio'));
    if (!is_dir($dir)) @mkdir($dir, 0755, true);
    $agora = (int) round(microtime(true) * 1000);
    $linhas = '';
    foreach ($lote as $x) {
        if (!is_array($x)) continue;
        $id = isset($x['id']) ? (string) $x['id'] : '';
        $v = isset($x['v']) ? (int) $x['v'] : 99;
        $t = isset($x['t']) ? (int) $x['t'] : 0;
        $c = isset($x['c']) ? trim(strip_tags((string) $x['c'])) : '';
        if (function_exists('mb_substr')) $c = mb_substr($c, 0, 800, 'UTF-8'); else $c = substr($c, 0, 1600);
        if (!isset($valido[$id]) || !in_array($v, array(1, -1, 0, 2), true)) continue;
        if ($t < 1700000000000 || $t > $agora + 86400000) $t = $agora;
        $linhas .= json_encode(array('id' => $id, 'v' => $v, 'c' => $c, 't' => $t, 's' => $agora), JSON_UNESCAPED_UNICODE) . "\n";
    }
    if ($linhas !== '' && file_put_contents($log, $linhas, FILE_APPEND | LOCK_EX) === false) sai(500, array('ok' => false, 'erro' => 'gravar'));
    sai(200, array('ok' => true));
}

$voto = array(); $coment = array();
if (is_file($log)) {
    $fh = fopen($log, 'r');
    if ($fh) {
        flock($fh, LOCK_SH);
        while (($l = fgets($fh)) !== false) {
            $x = json_decode($l, true);
            if (!is_array($x) || !isset($x['id'], $x['v'], $x['t'])) continue;
            $k = 'i' . $x['id'];
            if ((int) $x['v'] !== 2 && (!isset($voto[$k]) || $x['t'] >= $voto[$k][1])) $voto[$k] = array((int) $x['v'], (int) $x['t']);
            if (isset($x['c']) && $x['c'] !== '' && (!isset($coment[$k]) || $x['t'] >= $coment[$k][1])) $coment[$k] = array($x['c'], (int) $x['t']);
        }
        flock($fh, LOCK_UN);
        fclose($fh);
    }
}
$saida = new stdClass();
foreach (array_unique(array_merge(array_keys($voto), array_keys($coment))) as $k) {
    $v = isset($voto[$k]) ? $voto[$k] : array(0, 0);
    $c = isset($coment[$k]) ? $coment[$k] : array('', 0);
    $saida->{substr($k, 1)} = array($v[0], max($v[1], $c[1]), $c[0]);
}
sai(200, array('ok' => true, 'votos' => $saida));
