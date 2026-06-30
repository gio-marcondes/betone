import React, { useState, useEffect } from 'react';
import { 
  Play, Plus, Trash2, Key, RefreshCw, Layers, 
  TrendingUp, Activity, Compass, AlertCircle, FileCode, CheckCircle 
} from 'lucide-react';

export default function App() {
  const [urlInput, setUrlInput] = useState('');
  const [periodo, setPeriodo] = useState('ALL');
  const [jogos, setJogos] = useState([]); // [{id, nome, dados, manualMin, isManual}]
  const [abaAtiva, setAbaAtiva] = useState(null); // id do jogo ativo
  const [chaves, setChaves] = useState([]);
  const [novaChave, setNovaChave] = useState('');
  const [historico, setHistorico] = useState([]);
  const [showApiModal, setShowApiModal] = useState(false);
  const [statusMsg, setStatusMsg] = useState({ text: '', type: '' });

  const [jogosAoVivo, setJogosAoVivo] = useState([]);
  const [telegramToken, setTelegramToken] = useState('');
  const [telegramChatId, setTelegramChatId] = useState('');
  const [telegramEnabled, setTelegramEnabled] = useState(false);
  const [telegramMinProb, setTelegramMinProb] = useState(70);

  // Carregar chaves de API, histórico, configuração do telegram e jogos ao vivo
  useEffect(() => {
    fetchChaves();
    fetchHistorico();
    fetchTelegramConfig();
    fetchJogosAoVivo();
    const interval = setInterval(fetchJogosAoVivo, 30000); // atualiza a cada 30 segundos
    return () => clearInterval(interval);
  }, []);

  const fetchTelegramConfig = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/telegram/config');
      const data = await res.json();
      setTelegramToken(data.token || '');
      setTelegramChatId(data.chat_id || '');
      setTelegramEnabled(data.enabled || false);
      setTelegramMinProb(data.min_prob || 70);
    } catch (e) {
      console.log('Erro ao carregar configurações do Telegram.');
    }
  };

  const saveTelegramConfig = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/telegram/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: telegramToken.trim(),
          chat_id: telegramChatId.trim(),
          enabled: telegramEnabled,
          min_prob: Number(telegramMinProb)
        })
      });
      if (res.ok) {
        showStatus('Configurações do Telegram salvas com sucesso!');
      } else {
        throw new Error();
      }
    } catch (e) {
      showStatus('Erro ao salvar configurações do Telegram.', 'error');
    }
  };

  const testTelegramBot = async () => {
    showStatus('Enviando mensagem de teste...', 'info');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/telegram/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: telegramToken.trim(),
          chat_id: telegramChatId.trim(),
          enabled: true,
          min_prob: Number(telegramMinProb)
        })
      });
      const data = await res.json();
      if (data.status === 'ok') {
        showStatus('Mensagem de teste enviada! Verifique seu Telegram.');
      } else {
        showStatus(`Erro no teste: ${data.detail || 'Verifique as credenciais.'}`, 'error');
      }
    } catch (e) {
      showStatus('Erro de conexão ao testar robô.', 'error');
    }
  };

  const fetchJogosAoVivo = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/jogos/aovivo');
      const data = await res.json();
      setJogosAoVivo(data.jogos || []);
    } catch (e) {
      console.log('Erro ao carregar jogos ao vivo.');
    }
  };

  const fetchChaves = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/chaves');
      const data = await res.json();
      setChaves(data.chaves || []);
    } catch (e) {
      showStatus('Erro ao conectar com API Backend (FastAPI). Certifique-se de que está rodando.', 'error');
    }
  };

  const fetchHistorico = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/historico');
      const data = await res.json();
      setHistorico(data.historico || []);
    } catch (e) {
      console.log('Erro ao carregar histórico.');
    }
  };

  const showStatus = (text, type = 'success') => {
    setStatusMsg({ text, type });
    setTimeout(() => setStatusMsg({ text: '', type: '' }), 5000);
  };


  const addKey = async () => {
    if (!novaChave.trim()) return;
    try {
      const res = await fetch('http://127.0.0.1:8000/api/chaves', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chave: novaChave.trim() })
      });
      const data = await res.json();
      setChaves(data.chaves);
      setNovaChave('');
      showStatus('API Key adicionada com sucesso!');
    } catch (e) {
      showStatus('Erro ao adicionar chave API.', 'error');
    }
  };

  const definirChavePrincipal = async (key) => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/chaves/definir_padrao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chave: key })
      });
      const data = await res.json();
      setChaves(data.chaves);
      showStatus('Chave principal definida com sucesso!');
    } catch (e) {
      showStatus('Erro ao definir chave principal.', 'error');
    }
  };

  const removeKey = async (key) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/chaves/${key}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      setChaves(data.chaves);
      showStatus('Chave removida.');
    } catch (e) {
      showStatus('Erro ao remover chave ou limite mínimo atingido.', 'error');
    }
  };

  const abrirDoHistorico = (item) => {
    // Se o jogo já estiver aberto nas abas
    if (jogos.some(j => j.id === item.match_id)) {
      setAbaAtiva(item.match_id);
      return;
    }

    const novoJogo = {
      id: item.match_id,
      nome: item.nome,
      dados: null,
      manualMin: 45,
      isManual: false
    };

    setJogos(prev => [...prev, novoJogo]);
    setAbaAtiva(item.match_id);
    setTimeout(() => atualizarDadosJogo(item.match_id), 100);
  };

  const abrirJogoAoVivo = (item) => {
    if (jogos.some(j => j.id === item.match_id)) {
      setAbaAtiva(item.match_id);
      return;
    }

    const novoJogo = {
      id: item.match_id,
      nome: item.nome,
      dados: null,
      manualMin: item.minuto,
      isManual: false
    };

    setJogos(prev => [...prev, novoJogo]);
    setAbaAtiva(item.match_id);
    setTimeout(() => atualizarDadosJogo(item.match_id), 100);
  };


  const deletarDoHistorico = async (e, matchId) => {
    e.stopPropagation();
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/historico/${matchId}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      setHistorico(data.historico);
      showStatus('Jogo removido do histórico.');
    } catch (err) {
      showStatus('Erro ao deletar do histórico.', 'error');
    }
  };

  const adicionarJogo = async () => {
    if (!urlInput.trim()) return;
    showStatus('Buscando jogo...', 'info');
    
    let urlAlvo = urlInput.trim();
    let matchId = '';

    // Se não for um link direto (não contiver http), faz o scraping do nome
    if (!urlAlvo.includes('http')) {
      try {
        const resScrap = await fetch(`http://127.0.0.1:8000/api/jogo/buscar_scraping?q=${encodeURIComponent(urlAlvo)}`);
        if (!resScrap.ok) {
          const errData = await resScrap.json();
          throw new Error(errData.detail || 'Jogo não encontrado');
        }
        const dataScrap = await resScrap.json();
        urlAlvo = dataScrap.url;
        matchId = dataScrap.match_id;
        showStatus(`Jogo encontrado: ${urlAlvo}`, 'success');
      } catch (e) {
        showStatus(e.message || 'Erro ao realizar busca por nome no Sofascore.', 'error');
        return;
      }
    }

    try {
      const res = await fetch(`http://127.0.0.1:8000/api/jogo/detalhes?url=${encodeURIComponent(urlAlvo)}`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      
      const targetMatchId = data.match_id;
      const event = data.event;
      const casa = event.homeTeam?.shortName || event.homeTeam?.name || 'Casa';
      const fora = event.awayTeam?.shortName || event.awayTeam?.name || 'Fora';
      const nome = `${casa} x ${fora}`;

      // Recarregar histórico local
      fetchHistorico();

      // Verificar se já existe nas abas abertas
      if (jogos.some(j => j.id === targetMatchId)) {
        showStatus('Este jogo já está aberto em uma aba!', 'error');
        setAbaAtiva(targetMatchId);
        return;
      }

      const novoJogo = {
        id: targetMatchId,
        nome,
        dados: null,
        manualMin: 45,
        isManual: false
      };

      setJogos(prev => [...prev, novoJogo]);
      setAbaAtiva(targetMatchId);
      setUrlInput('');
      
      // Atualiza estatísticas do jogo adicionado
      atualizarDadosJogo(targetMatchId);
    } catch (e) {
      showStatus('Não foi possível obter os detalhes do jogo. Verifique o termo ou a URL.', 'error');
    }
  };

  const atualizarDadosJogo = async (matchId) => {
    const jogo = jogos.find(j => j.id === matchId);
    const minParam = (jogo && jogo.isManual) ? `&minuto=${jogo.manualMin}` : '';
    
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/jogo/estatisticas/${matchId}?periodo=${periodo}${minParam}`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      
      setJogos(prev => prev.map(j => {
        if (j.id === matchId) {
          return {
            ...j,
            dados: data,
            // Sincroniza minuto se não estiver manual
            manualMin: j.isManual ? j.manualMin : data.minuto
          };
        }
        return j;
      }));
    } catch (e) {
      showStatus('Erro ao atualizar estatísticas da API.', 'error');
    }
  };

  const carregarSimulacaoLocal = async () => {
    showStatus('Carregando dados locais...', 'info');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/jogo/simular', { method: 'POST' });
      if (!res.ok) throw new Error();
      const data = await res.json();
      
      const mockId = 'offline_sim';
      const novoJogo = {
        id: mockId,
        nome: `${data.home} x ${data.away} (Offline)`,
        dados: data,
        manualMin: data.minuto,
        isManual: false
      };

      setJogos(prev => {
        const filtrado = prev.filter(j => j.id !== mockId);
        return [...filtrado, novoJogo];
      });
      setAbaAtiva(mockId);
      showStatus('Simulação local carregada!');
    } catch (e) {
      showStatus('Erro ao ler a.json no backend.', 'error');
    }
  };

  const fecharJogo = (id) => {
    setJogos(prev => prev.filter(j => j.id !== id));
    if (abaAtiva === id) {
      const restantes = jogos.filter(j => j.id !== id);
      setAbaAtiva(restantes.length > 0 ? restantes[0].id : null);
    }
  };

  const setMinutoManual = (id, minVal) => {
    setJogos(prev => prev.map(j => {
      if (j.id === id) {
        return { ...j, manualMin: Number(minVal), isManual: true };
      }
      return j;
    }));
  };

  const resetMinutoAuto = (id) => {
    setJogos(prev => prev.map(j => {
      if (j.id === id) {
        return { ...j, isManual: false };
      }
      return j;
    }));
    setTimeout(() => atualizarDadosJogo(id), 100);
  };

  const getProbColor = (prob) => {
    if (prob >= 68) return 'from-emerald-600 to-green-500'; // FORTE
    if (prob >= 56) return 'from-green-600 to-teal-500';    // BOA
    if (prob >= 48) return 'from-yellow-600 to-amber-500';  // OBSERVAR
    return 'from-rose-600 to-red-500';                      // FRACA
  };

  const getProbText = (prob) => {
    if (prob >= 68) return '🟢 OPORTUNIDADE EXCELENTE';
    if (prob >= 56) return '🟡 BOA OPERAÇÃO';
    if (prob >= 48) return '⚪ ATENÇÃO / OBSERVAR';
    return '🔴 NÃO RECOMENDADO';
  };

  const jogoAtivoObj = jogos.find(j => j.id === abaAtiva);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0b0c10', color: '#c5c6c7' }}>
      
      {/* Menu / Sidebar Lateral do Histórico e Jogos Ao Vivo */}
      <div style={{
        width: '300px',
        backgroundColor: '#11131e',
        borderRight: '1px solid #1f2335',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        padding: '20px',
        overflowY: 'auto'
      }}>
        {/* Seção 1: Jogos Ao Vivo */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #1f2335', paddingBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity style={{ color: '#ef4444' }} size={18} />
              <h2 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#fff', letterSpacing: '0.5px' }}>JOGOS AO VIVO</h2>
            </div>
            <button 
              onClick={fetchJogosAoVivo} 
              style={{ background: 'transparent', border: 'none', color: '#8f93a2', cursor: 'pointer' }}
              title="Atualizar lista ao vivo"
            >
              <RefreshCw size={14} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' }}>
            {jogosAoVivo.length > 0 ? (
              jogosAoVivo.map((item, idx) => (
                <div 
                  key={idx}
                  onClick={() => abrirJogoAoVivo(item)}
                  style={{
                    padding: '10px 12px',
                    backgroundColor: '#161824',
                    borderRadius: '8px',
                    border: '1px solid #1f2335',
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#ef4444';
                    e.currentTarget.style.transform = 'translateX(2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#1f2335';
                    e.currentTarget.style.transform = 'none';
                  }}
                >
                  <span style={{ fontSize: '0.82rem', fontWeight: 'bold', color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {item.nome}
                  </span>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                    <span style={{ 
                      color: item.status === 'Finalizado' ? '#8f93a2' : item.status === 'Intervalo' ? '#f59e0b' : '#ef4444', 
                      fontWeight: 'bold', 
                      backgroundColor: item.status === 'Finalizado' ? '#1f2335' : item.status === 'Intervalo' ? '#f59e0b22' : '#ef444422', 
                      padding: '1px 6px', 
                      borderRadius: '4px' 
                    }}>
                      {item.status || `${item.minuto}'`}
                    </span>
                    <span style={{ color: '#a6e3a1', fontWeight: 'bold', fontFamily: 'monospace' }}>
                      {item.placar}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ textAlign: 'center', color: '#8f93a2', fontSize: '0.78rem', padding: '15px 0' }}>
                Nenhum jogo ao vivo no momento.
              </div>
            )}
          </div>
        </div>

        {/* Seção 2: Histórico Salvo */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid #1f2335', paddingBottom: '10px' }}>
            <Layers style={{ color: '#10b981' }} size={18} />
            <h2 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#fff', letterSpacing: '0.5px' }}>HISTÓRICO SALVO</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto' }}>
            {historico.length > 0 ? (
              historico.map((item, idx) => (
                <div 
                  key={idx}
                  onClick={() => abrirDoHistorico(item)}
                  style={{
                    padding: '10px 12px',
                    backgroundColor: '#161824',
                    borderRadius: '8px',
                    border: '1px solid #1f2335',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '0.82rem',
                    fontWeight: '500',
                    color: '#cdd6f4',
                    transition: 'border-color 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = '#10b981'}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = '#1f2335'}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', overflow: 'hidden' }}>
                    <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: '#fff' }}>{item.nome}</span>
                    <span style={{ fontSize: '0.72rem', color: '#8f93a2' }}>ID: {item.match_id}</span>
                  </div>
                  <button 
                    onClick={(e) => deletarDoHistorico(e, item.match_id)}
                    style={{
                      background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', opacity: 0.7
                    }}
                    title="Remover do histórico"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))
            ) : (
              <div style={{ textAlign: 'center', color: '#8f93a2', fontSize: '0.78rem', padding: '15px 0' }}>
                Nenhum jogo salvo.
              </div>
            )}
          </div>
        </div>
      </div>


      {/* Conteúdo Principal do Dashboard */}
      <div style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '1200px' }}>
        
        {/* Barra de Status Temporário */}
        {statusMsg.text && (
          <div style={{
            padding: '12px 20px',
            borderRadius: '8px',
            backgroundColor: statusMsg.type === 'error' ? '#ef444422' : statusMsg.type === 'info' ? '#3b82f622' : '#10b98122',
            border: `1px solid ${statusMsg.type === 'error' ? '#ef444455' : statusMsg.type === 'info' ? '#3b82f655' : '#10b98155'}`,
            color: statusMsg.type === 'error' ? '#fca5a5' : statusMsg.type === 'info' ? '#93c5fd' : '#a7f3d0',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            <AlertCircle size={18} />
            <span>{statusMsg.text}</span>
          </div>
        )}

        {/* Header / Barra de Controles Superior */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '15px',
          backgroundColor: '#11131e',
          padding: '15px 25px',
          borderRadius: '12px',
          border: '1px solid #1f2335'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Activity size={24} style={{ color: '#10b981' }} />
            <h1 style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#fff', letterSpacing: '0.5px' }}>
              PREDATOR SCANNER <span style={{ color: '#10b981', fontSize: '0.8rem' }}>WEB PRO</span>
            </h1>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <input 
              type="text" 
              placeholder="Time A Time B (ou URL Sofascore)..."
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              style={{
                padding: '8px 12px',
                backgroundColor: '#0b0c10',
                border: '1px solid #2f354f',
                borderRadius: '6px',
                color: '#fff',
                outline: 'none',
                width: '280px'
              }}
            />
            <button 
              onClick={adicionarJogo}
              style={{
                backgroundColor: '#10b981',
                color: '#0b0c10',
                fontWeight: 'bold',
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Plus size={16} /> Adicionar
            </button>
            
            <button 
              onClick={carregarSimulacaoLocal}
              style={{
                backgroundColor: '#f59e0b',
                color: '#0b0c10',
                fontWeight: 'bold',
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <FileCode size={16} /> Testar JSON
            </button>

            <div style={{ height: '24px', width: '1px', backgroundColor: '#2f354f' }} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.85rem', color: '#8f93a2' }}>Período:</span>
              <select 
                value={periodo} 
                onChange={(e) => {
                  setPeriodo(e.target.value);
                  // Forçar atualização de todos
                  setTimeout(() => jogos.forEach(j => atualizarDadosJogo(j.id)), 100);
                }}
                style={{
                  backgroundColor: '#0b0c10',
                  border: '1px solid #2f354f',
                  color: '#fff',
                  padding: '6px 12px',
                  borderRadius: '6px'
                }}
              >
                <option value="ALL">Jogo Inteiro</option>
                <option value="1ST">1º Tempo</option>
                <option value="2ND">2º Tempo</option>
              </select>
            </div>

            <button 
              onClick={() => setShowApiModal(!showApiModal)}
              style={{
                backgroundColor: '#1f2335',
                color: '#c5c6c7',
                padding: '8px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer'
              }}
              title="Gerenciar API Keys"
            >
              <Key size={18} />
            </button>
          </div>
        </div>

        {/* Modal de API Keys & Telegram Config */}
        {showApiModal && (
          <div style={{
            backgroundColor: '#11131e',
            padding: '20px',
            borderRadius: '12px',
            border: '1px solid #1f2335',
            display: 'grid',
            gridTemplateColumns: '1fr 1.2fr',
            gap: '30px'
          }}>
            {/* Coluna 1: API Keys */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <h3 style={{ color: '#fff', fontSize: '1rem', fontWeight: 'bold', borderBottom: '1px solid #1f2335', paddingBottom: '8px' }}>
                🔑 Chaves API Sofascore
              </h3>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input 
                  type="text" 
                  placeholder="Adicionar Nova Chave..."
                  value={novaChave}
                  onChange={(e) => setNovaChave(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    backgroundColor: '#0b0c10',
                    border: '1px solid #2f354f',
                    color: '#fff',
                    borderRadius: '6px',
                    fontSize: '0.85rem'
                  }}
                />
                <button onClick={addKey} style={{
                  backgroundColor: '#10b981', color: '#0b0c10', border: 'none', borderRadius: '6px', padding: '8px 16px', fontWeight: 'bold', cursor: 'pointer', fontSize: '0.85rem'
                }}>Adicionar</button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '180px', overflowY: 'auto' }}>
                {chaves.map((k, idx) => (
                  <div key={idx} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#0f111a', padding: '8px 12px', borderRadius: '6px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      {idx === 0 ? (
                        <span style={{ fontSize: '0.7rem', fontWeight: 'bold', padding: '2px 6px', backgroundColor: '#10b98122', color: '#10b981', borderRadius: '4px' }}>
                          Ativa
                        </span>
                      ) : (
                        <button 
                          onClick={() => definirChavePrincipal(k)}
                          style={{
                            fontSize: '0.7rem', fontWeight: 'bold', padding: '2px 6px', backgroundColor: '#1f2335', color: '#c5c6c7', border: 'none', borderRadius: '4px', cursor: 'pointer'
                          }}
                        >
                          Ativar
                        </button>
                      )}
                      <span style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{k.slice(0, 10)}...{k.slice(-6)}</span>
                    </div>
                    <button onClick={() => removeKey(k)} style={{
                      backgroundColor: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer'
                    }}><Trash2 size={14} /></button>
                  </div>
                ))}
              </div>
            </div>

            {/* Coluna 2: Telegram Bot Config */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', borderLeft: '1px solid #1f2335', paddingLeft: '30px' }}>
              <h3 style={{ color: '#fff', fontSize: '1rem', fontWeight: 'bold', borderBottom: '1px solid #1f2335', paddingBottom: '8px' }}>
                🤖 Robô do Telegram
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#8f93a2', display: 'block', marginBottom: '4px' }}>Token do Bot:</label>
                  <input 
                    type="password" 
                    placeholder="Ex: 123456789:ABCdefGhI..."
                    value={telegramToken}
                    onChange={(e) => setTelegramToken(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      backgroundColor: '#0b0c10',
                      border: '1px solid #2f354f',
                      color: '#fff',
                      borderRadius: '6px',
                      fontSize: '0.85rem'
                    }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <label style={{ fontSize: '0.8rem', color: '#8f93a2', display: 'block', marginBottom: '4px' }}>Chat ID / Canal:</label>
                    <input 
                      type="text" 
                      placeholder="Ex: -100123456789"
                      value={telegramChatId}
                      onChange={(e) => setTelegramChatId(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        backgroundColor: '#0b0c10',
                        border: '1px solid #2f354f',
                        color: '#fff',
                        borderRadius: '6px',
                        fontSize: '0.85rem'
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '0.8rem', color: '#8f93a2', display: 'block', marginBottom: '4px' }}>Confiança Mínima (%):</label>
                    <input 
                      type="number" 
                      min="50"
                      max="100"
                      value={telegramMinProb}
                      onChange={(e) => setTelegramMinProb(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        backgroundColor: '#0b0c10',
                        border: '1px solid #2f354f',
                        color: '#fff',
                        borderRadius: '6px',
                        fontSize: '0.85rem',
                        textAlign: 'center'
                      }}
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '5px' }}>
                  <input 
                    type="checkbox" 
                    id="tg_enabled"
                    checked={telegramEnabled}
                    onChange={(e) => setTelegramEnabled(e.target.checked)}
                    style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                  />
                  <label htmlFor="tg_enabled" style={{ fontSize: '0.85rem', color: '#c5c6c7', cursor: 'pointer', fontWeight: 'bold' }}>
                    Ativar Robô de Sinais Automatizados
                  </label>
                </div>

                <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                  <button 
                    onClick={saveTelegramConfig} 
                    style={{
                      flex: 1, backgroundColor: '#10b981', color: '#0b0c10', border: 'none', borderRadius: '6px', padding: '8px 12px', fontWeight: 'bold', cursor: 'pointer', fontSize: '0.85rem'
                    }}
                  >
                    Salvar
                  </button>
                  <button 
                    onClick={testTelegramBot} 
                    style={{
                      flex: 1, backgroundColor: '#1f2335', color: '#fff', border: '1px solid #2f354f', borderRadius: '6px', padding: '8px 12px', fontWeight: 'bold', cursor: 'pointer', fontSize: '0.85rem'
                    }}
                  >
                    Enviar Teste
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}


        {/* Abas dos Jogos (Tab Bar) */}
        {jogos.length > 0 && (
          <div style={{ display: 'flex', gap: '5px', overflowX: 'auto', paddingBottom: '5px' }}>
            {jogos.map(j => (
              <div 
                key={j.id}
                onClick={() => setAbaAtiva(j.id)}
                style={{
                  backgroundColor: abaAtiva === j.id ? '#161824' : '#11131e',
                  border: '1px solid #1f2335',
                  borderBottom: abaAtiva === j.id ? '2px solid #10b981' : '1px solid #1f2335',
                  padding: '10px 18px',
                  borderRadius: '8px 8px 0 0',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  color: abaAtiva === j.id ? '#10b981' : '#c5c6c7',
                  fontWeight: 'bold',
                  fontSize: '0.9rem',
                  whiteSpace: 'nowrap'
                }}
              >
                <span>{j.nome}</span>
                <button 
                  onClick={(e) => { e.stopPropagation(); fecharJogo(j.id); }}
                  style={{
                    background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', display: 'flex', alignItems: 'center'
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Layout de Conteúdo do Jogo Selecionado */}
        {jogoAtivoObj && jogoAtivoObj.dados ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {/* Placar e Painel de Informações do Jogo */}
            <div style={{
              backgroundColor: '#161824',
              padding: '20px 30px',
              borderRadius: '12px',
              border: '1px solid #1f2335',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <span style={{ fontSize: '0.8rem', color: '#8f93a2', textTransform: 'uppercase', letterSpacing: '1px' }}>Time Mandante</span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#89b4fa' }}>{jogoAtivoObj.dados.home}</h2>
                
                {jogoAtivoObj.dados.ap && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: '#8f93a2', width: '28px' }}>AP1</span>
                      <div style={{ width: '80px', height: '5px', backgroundColor: '#0b0c10', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${jogoAtivoObj.dados.ap.ap1_home}%`, height: '100%', backgroundColor: '#10b981' }} />
                      </div>
                      <span style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 'bold' }}>{Math.round(jogoAtivoObj.dados.ap.ap1_home)}%</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: '#8f93a2', width: '28px' }}>AP2</span>
                      <div style={{ width: '80px', height: '5px', backgroundColor: '#0b0c10', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${jogoAtivoObj.dados.ap.ap2_home}%`, height: '100%', backgroundColor: '#f59e0b' }} />
                      </div>
                      <span style={{ fontSize: '0.72rem', color: '#f59e0b', fontWeight: 'bold' }}>{Math.round(jogoAtivoObj.dados.ap.ap2_home)}%</span>
                    </div>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#fff', letterSpacing: '3px' }}>
                  {jogoAtivoObj.dados.placar}
                </div>
                <div style={{
                  backgroundColor: '#10b98122',
                  color: '#10b981',
                  padding: '4px 12px',
                  borderRadius: '20px',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <Play size={12} fill="#10b981" /> Minuto {jogoAtivoObj.dados.minuto}'
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '5px' }}>
                <span style={{ fontSize: '0.8rem', color: '#8f93a2', textTransform: 'uppercase', letterSpacing: '1px' }}>Time Visitante</span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#f9e2af' }}>{jogoAtivoObj.dados.away}</h2>

                {jogoAtivoObj.dados.ap && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '8px', alignItems: 'flex-end' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 'bold' }}>{Math.round(jogoAtivoObj.dados.ap.ap1_away)}%</span>
                      <div style={{ width: '80px', height: '5px', backgroundColor: '#0b0c10', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${jogoAtivoObj.dados.ap.ap1_away}%`, height: '100%', backgroundColor: '#10b981' }} />
                      </div>
                      <span style={{ fontSize: '0.72rem', color: '#8f93a2', width: '28px', textAlign: 'right' }}>AP1</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.72rem', color: '#f59e0b', fontWeight: 'bold' }}>{Math.round(jogoAtivoObj.dados.ap.ap2_away)}%</span>
                      <div style={{ width: '80px', height: '5px', backgroundColor: '#0b0c10', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${jogoAtivoObj.dados.ap.ap2_away}%`, height: '100%', backgroundColor: '#f59e0b' }} />
                      </div>
                      <span style={{ fontSize: '0.72rem', color: '#8f93a2', width: '28px', textAlign: 'right' }}>AP2</span>
                    </div>
                  </div>
                )}
              </div>
            </div>


            {/* Área de Controles do Minuto e Atualização */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: '#11131e',
              padding: '12px 25px',
              borderRadius: '10px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                <span style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>Definir Minuto Manual:</span>
                <input 
                  type="number" 
                  value={jogoAtivoObj.manualMin}
                  onChange={(e) => setMinutoManual(jogoAtivoObj.id, e.target.value)}
                  style={{
                    width: '60px',
                    backgroundColor: '#0b0c10',
                    border: '1px solid #2f354f',
                    color: '#fff',
                    borderRadius: '6px',
                    padding: '5px',
                    textAlign: 'center',
                    fontWeight: 'bold'
                  }}
                />
                {jogoAtivoObj.isManual && (
                  <button 
                    onClick={() => resetMinutoAuto(jogoAtivoObj.id)}
                    style={{
                      backgroundColor: '#1f2335', color: '#c5c6c7', border: 'none', padding: '5px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem'
                    }}
                  >
                    Voltar Automático (API)
                  </button>
                )}
              </div>

              <button 
                onClick={() => atualizarDadosJogo(jogoAtivoObj.id)}
                style={{
                  backgroundColor: '#1f2335',
                  color: '#fff',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontWeight: 'bold'
                }}
              >
                <RefreshCw size={14} /> Atualizar Agora
              </button>
            </div>

            {/* Divisão Principal: Estatísticas x Oportunidades */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
              
              {/* Esquerda: Matriz de Estatísticas Traduzidas */}
              <div style={{
                backgroundColor: '#11131e',
                borderRadius: '12px',
                border: '1px solid #1f2335',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '15px'
              }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 'bold', color: '#fff', borderBottom: '1px solid #1f2335', paddingBottom: '10px' }}>
                  📊 Estatísticas Traduzidas (Sofascore)
                </h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '550px', overflowY: 'auto' }}>
                  {jogoAtivoObj.dados.estatisticas.map((stat, index) => {
                    const total = stat.home_val + stat.away_val || 1;
                    const homePercent = (stat.home_val / total) * 100;
                    
                    return (
                      <div key={index} style={{
                        backgroundColor: '#161824',
                        padding: '10px 15px',
                        borderRadius: '8px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 'bold', color: '#89b4fa', fontSize: '0.9rem' }}>{stat.home}</span>
                          <span style={{ fontSize: '0.85rem', color: '#cdd6f4', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{stat.nome}</span>
                          <span style={{ fontWeight: 'bold', color: '#f9e2af', fontSize: '0.9rem' }}>{stat.away}</span>
                        </div>
                        {/* Barra de comparação visual */}
                        <div style={{ height: '6px', width: '100%', backgroundColor: '#2f354f', borderRadius: '4px', display: 'flex', overflow: 'hidden' }}>
                          <div style={{ width: `${homePercent}%`, backgroundColor: '#89b4fa', height: '100%' }} />
                          <div style={{ width: `${100 - homePercent}%`, backgroundColor: '#f9e2af', height: '100%' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Direita: Oportunidades e Sugestões Operacionais */}
              <div style={{
                backgroundColor: '#11131e',
                borderRadius: '12px',
                border: '1px solid #1f2335',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '15px'
              }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 'bold', color: '#fff', borderBottom: '1px solid #1f2335', paddingBottom: '10px' }}>
                  🚀 Oportunidades & Cenários de Valor
                </h3>

                <div style={{ display: 'flex', gap: '15px', marginBottom: '10px' }}>
                  <div style={{
                    flex: 1, backgroundColor: '#161824', padding: '12px', borderRadius: '8px', textAlign: 'center', border: '1px solid #2f354f'
                  }}>
                    <span style={{ fontSize: '0.8rem', color: '#8f93a2' }}>Projeção de Gols</span>
                    <div style={{ fontSize: '1.35rem', fontWeight: 'bold', color: '#10b981', marginTop: '4px' }}>
                      {jogoAtivoObj.dados.analise.proj_gols} Gols
                    </div>
                  </div>
                  
                  <div style={{
                    flex: 1, backgroundColor: '#161824', padding: '12px', borderRadius: '8px', textAlign: 'center', border: '1px solid #2f354f'
                  }}>
                    <span style={{ fontSize: '0.8rem', color: '#8f93a2' }}>Projeção de Cantos</span>
                    <div style={{ fontSize: '1.35rem', fontWeight: 'bold', color: '#89b4fa', marginTop: '4px' }}>
                      {jogoAtivoObj.dados.analise.proj_cantos} Cantos
                    </div>
                  </div>
                </div>

                {/* Cards de Oportunidades */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                  {jogoAtivoObj.dados.analise.sugestoes.map((sug, idx) => (
                    <div key={idx} style={{
                      borderRadius: '10px',
                      overflow: 'hidden',
                      border: '1px solid #2f354f',
                      backgroundColor: '#161824'
                    }}>
                      <div style={{
                        background: `linear-gradient(to right, ${getProbColor(sug.probabilidade)})`,
                        height: '4px',
                        width: '100%'
                      }} />

                      <div style={{ padding: '15px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 'bold', fontSize: '0.95rem' }}>{sug.mercado}</span>
                          <span style={{
                            fontSize: '0.75rem',
                            fontWeight: 'bold',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            backgroundColor: '#0b0c10',
                            color: '#fff'
                          }}>
                            {getProbText(sug.probabilidade)}
                          </span>
                        </div>

                        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
                          <div>
                            <span style={{ fontSize: '0.8rem', color: '#8f93a2' }}>Seleção Sugerida:</span>
                            <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#10b981' }}>{sug.selecao}</div>
                          </div>

                          <div>
                            <span style={{ fontSize: '0.8rem', color: '#8f93a2' }}>Probabilidade:</span>
                            <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff' }}>{sug.probabilidade}%</div>
                          </div>

                          <div>
                            <span style={{ fontSize: '0.8rem', color: '#8f93a2' }}>Odd Mínima:</span>
                            <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#f59e0b' }}>{sug.odd_justa}</div>
                          </div>
                        </div>

                        <div style={{
                          fontSize: '0.8rem',
                          color: '#a6adc8',
                          backgroundColor: '#11131e',
                          padding: '8px 12px',
                          borderRadius: '6px',
                          marginTop: '5px'
                        }}>
                          💡 {sug.raciocinio}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

              </div>

            </div>

          </div>
        ) : (
          <div style={{
            padding: '80px 20px',
            textAlign: 'center',
            backgroundColor: '#11131e',
            borderRadius: '12px',
            border: '1px solid #1f2335',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '15px'
          }}>
            <Compass size={48} style={{ color: '#2f354f' }} />
            <h3 style={{ color: '#fff', fontWeight: 'bold' }}>Nenhum jogo aberto</h3>
            <p style={{ color: '#8f93a2', maxWidth: '400px', fontSize: '0.9rem' }}>
              Insira o nome de dois times no topo (ex: <strong>ceará botafogo</strong>) para iniciar a busca automatizada via Selenium, ou recarregue um jogo antigo pelo menu lateral esquerdo.
            </p>
          </div>
        )}

      </div>

    </div>
  );
}
