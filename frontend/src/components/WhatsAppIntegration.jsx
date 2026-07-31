import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';

const WhatsAppIntegration = () => {
    const [qrCodeStatus, setQrCodeStatus] = useState('LOADING'); // LOADING, STARTING, WAITING_FOR_SCAN, WORKING, ERROR
    const [qrCodeImage, setQrCodeImage] = useState(null);
    const [message, setMessage] = useState('Carregando status do WhatsApp...');
    
    // Novos estados
    const [pairingMethod, setPairingMethod] = useState('QRCODE'); // QRCODE, PHONE
    const [phoneNumber, setPhoneNumber] = useState('');
    const [pairingCode, setPairingCode] = useState(null);
    const [isRequestingCode, setIsRequestingCode] = useState(false);
    
    // Ref para controle de polling
    const pollingInterval = useRef(null);

    const fetchQRCode = async () => {
        const fetchUrl = `/api/whatsapp/qrcode/${Date.now()}/?t=${new Date().getTime()}`;
        setQrCodeStatus('LOADING');
        setMessage('Buscando status da conexão...');
        setQrCodeImage(null);
        
        try {
            const response = await api.get(fetchUrl);
            const data = response.data;

            setQrCodeStatus(data.status || 'SUCCESS');
            setMessage(data.message || 'QR Code recebido.');
            
            if (data.qrcode_base64) {
                setQrCodeImage(`data:image/png;base64,${data.qrcode_base64}`);
            }
        } catch (error) {
            console.error("Erro na requisição Axios:", error);
            setQrCodeStatus('ERROR');
            const erroApi = error.response?.data?.error || 'Erro ao conectar com o serviço do WhatsApp.';
            setMessage(erroApi);
        }
    };

    const requestPairingCode = async () => {
        if (!phoneNumber || phoneNumber.length < 10) {
            setMessage('Por favor, digite um número de telefone válido com DDD.');
            return;
        }

        setIsRequestingCode(true);
        setMessage('Gerando código de parelhamento...');
        setPairingCode(null);

        try {
            const response = await api.post('/api/whatsapp/pairing-code/', {
                phoneNumber: phoneNumber
            });
            const data = response.data;
            
            setQrCodeStatus(data.status || 'WAITING_FOR_SCAN');
            setPairingCode(data.code);
            setMessage(data.message || 'Código gerado com sucesso!');
        } catch (error) {
            console.error("Erro ao solicitar código:", error);
            const erroApi = error.response?.data?.error || 'Erro ao gerar o código. Tente novamente.';
            setMessage(erroApi);
        } finally {
            setIsRequestingCode(false);
        }
    };

    const checkStatus = async () => {
        try {
            const response = await api.get(`/api/whatsapp/status/?t=${new Date().getTime()}`);
            const data = response.data;
            if (data.status === 'WORKING' || data.status === 'CONNECTED') {
                setQrCodeStatus('WORKING');
                setMessage('O WhatsApp já está conectado e pronto para uso!');
                setPairingCode(null);
            }
        } catch (error) {
            console.error("Erro ao checar status:", error);
        }
    };

    const handleDisconnect = async () => {
        setQrCodeStatus('LOADING');
        setMessage('Desconectando WhatsApp...');
        try {
            await api.delete('/api/whatsapp/qrcode/');
            setPairingCode(null);
            setPhoneNumber('');
            if (pairingMethod === 'QRCODE') {
                fetchQRCode();
            } else {
                setQrCodeStatus('WAITING_FOR_SCAN');
                setMessage('Desconectado. Insira seu número para gerar um novo código.');
            }
        } catch (error) {
            setQrCodeStatus('WORKING');
            setMessage('Erro ao tentar desconectar. Tente novamente.');
        }
    };

    // Efeito para carregar o estado inicial e fazer polling
    useEffect(() => {
        if (pairingMethod === 'QRCODE' && qrCodeStatus !== 'WORKING') {
            fetchQRCode();
        } else if (pairingMethod === 'PHONE' && qrCodeStatus !== 'WORKING') {
            checkStatus();
        }

        // Configura o polling para checar se conectou
        pollingInterval.current = setInterval(() => {
            if (pairingMethod === 'PHONE' && pairingCode && qrCodeStatus !== 'WORKING') {
                checkStatus();
            } else if (pairingMethod === 'QRCODE' && qrCodeStatus !== 'WORKING') {
                fetchQRCode();
            }
        }, 10000); // 10 segundos

        return () => {
            if (pollingInterval.current) {
                clearInterval(pollingInterval.current);
            }
        };
    }, [pairingMethod]);

    return (
        <div className="bg-background-paper border border-white/5 p-6 rounded-xl w-full flex flex-col items-center text-center">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-green-500">📱</span> Integração WhatsApp
            </h3>

            {qrCodeStatus !== 'WORKING' && (
                <div className="flex w-full mb-6 bg-background-darker p-1 rounded-lg">
                    <button 
                        onClick={() => { setPairingMethod('QRCODE'); setPairingCode(null); }}
                        className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${pairingMethod === 'QRCODE' ? 'bg-gold text-black' : 'text-gray-400 hover:text-white'}`}
                    >
                        QR Code
                    </button>
                    <button 
                        onClick={() => { setPairingMethod('PHONE'); setQrCodeImage(null); }}
                        className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${pairingMethod === 'PHONE' ? 'bg-gold text-black' : 'text-gray-400 hover:text-white'}`}
                    >
                        Código de Telefone
                    </button>
                </div>
            )}
            
            <p className="text-sm text-gray-400 mb-6">{message}</p>

            {/* SESSÃO DE QR CODE */}
            {pairingMethod === 'QRCODE' && qrCodeStatus !== 'WORKING' && (
                <>
                    {qrCodeStatus === 'WAITING_FOR_SCAN' && qrCodeImage && (
                        <div className="flex justify-center mb-6 bg-white p-2 rounded-lg">
                            <img 
                                src={qrCodeImage} 
                                alt="WhatsApp QR Code" 
                                style={{ width: '200px', height: '200px' }}
                            />
                        </div>
                    )}

                    {['LOADING', 'STARTING', 'WAITING_FOR_SCAN', 'ERROR'].includes(qrCodeStatus) && (
                        <div className="flex gap-2 w-full mt-auto">
                            <button 
                                onClick={fetchQRCode}
                                disabled={qrCodeStatus === 'LOADING'}
                                className={`flex-1 font-bold py-2 px-2 rounded-lg transition-all text-xs border 
                                    ${qrCodeStatus === 'LOADING' 
                                        ? 'bg-gray-700 border-gray-600 text-gray-400 cursor-not-allowed' 
                                        : 'bg-background-darker border-white/10 hover:border-gold text-white'}`}
                            >
                                {qrCodeStatus === 'LOADING' ? '⏳ Carregando...' : '🔄 Atualizar'}
                            </button>
                            <button 
                                onClick={handleDisconnect}
                                className="flex-1 bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 text-red-400 font-bold py-2 px-2 rounded-lg transition-all text-xs"
                                title="Força a exclusão da sessão travada"
                            >
                                🔌 Forçar Reset
                            </button>
                        </div>
                    )}
                </>
            )}

            {/* SESSÃO DE TELEFONE */}
            {pairingMethod === 'PHONE' && qrCodeStatus !== 'WORKING' && (
                <div className="w-full flex flex-col items-center">
                    {!pairingCode ? (
                        <>
                            <input
                                type="text"
                                placeholder="DDD + Número (Ex: 11999999999)"
                                value={phoneNumber}
                                onChange={(e) => setPhoneNumber(e.target.value)}
                                className="w-full bg-background-darker border border-white/10 rounded-lg p-3 text-white mb-4 text-center focus:border-gold focus:outline-none"
                            />
                            <button 
                                onClick={requestPairingCode}
                                disabled={isRequestingCode}
                                className={`w-full font-bold py-3 px-4 rounded-lg transition-all text-sm border 
                                    ${isRequestingCode 
                                        ? 'bg-gray-700 border-gray-600 text-gray-400 cursor-not-allowed' 
                                        : 'bg-gold border-gold text-black hover:bg-yellow-500'}`}
                            >
                                {isRequestingCode ? '⏳ Gerando...' : 'Gerar Código de Conexão'}
                            </button>
                        </>
                    ) : (
                        <div className="w-full">
                            <div className="bg-background-darker border border-gold/50 rounded-lg p-6 mb-4">
                                <span className="text-4xl font-mono font-bold tracking-[0.25em] text-white">
                                    {pairingCode}
                                </span>
                            </div>
                            <div className="text-xs text-gray-400 text-left space-y-2 mb-4 bg-white/5 p-3 rounded">
                                <p>1. Abra o WhatsApp no celular</p>
                                <p>2. Vá em Configurações &gt; Aparelhos conectados</p>
                                <p>3. Toque em "Conectar um aparelho"</p>
                                <p>4. Escolha "Conectar com número de telefone"</p>
                                <p>5. Digite o código acima</p>
                            </div>
                            <button 
                                onClick={() => setPairingCode(null)}
                                className="w-full font-bold py-2 px-4 rounded-lg bg-background-darker border border-white/10 hover:border-white/30 text-white text-sm"
                            >
                                Gerar Novo Código
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Sucesso - Sessão Conectada */}
            {qrCodeStatus === 'WORKING' && (
                <div className="flex flex-col items-center justify-center w-full mt-2 space-y-6">
                    <div className="w-20 h-20 bg-green-500/10 text-green-500 border border-green-500/20 rounded-full flex items-center justify-center text-4xl shadow-[0_0_15px_rgba(34,197,94,0.3)]">
                        ✅
                    </div>
                    
                    <div className="text-green-500 font-bold text-center">
                        Status: Sistema Conectado com Sucesso!
                    </div>

                    <button 
                        onClick={handleDisconnect}
                        className="w-full bg-red-500/10 border border-red-500/30 hover:bg-red-500/20 text-red-400 font-bold py-3 px-4 rounded-lg transition-all text-sm"
                    >
                        Desconectar WhatsApp
                    </button>
                </div>
            )}
        </div>
    );
};

export default WhatsAppIntegration;
