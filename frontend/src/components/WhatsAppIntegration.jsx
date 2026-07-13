import React, { useState, useEffect } from 'react';
import api from '../services/api';

const WhatsAppIntegration = () => {
    const [qrCodeStatus, setQrCodeStatus] = useState('LOADING'); // LOADING, STARTING, WAITING_FOR_SCAN, WORKING, ERROR
    const [qrCodeImage, setQrCodeImage] = useState(null);
    const [message, setMessage] = useState('Carregando status do WhatsApp...');

    const fetchQRCode = async () => {
        setQrCodeStatus('LOADING');
        setMessage('Buscando status da conexão...');
        setQrCodeImage(null);
        
        try {
            // Adiciona timestamp para evitar cache do navegador e garantir que a requisição chegue ao Gunicorn
            const response = await api.get(`/api/whatsapp/qrcode/?t=${new Date().getTime()}`);
            const data = response.data;

            setQrCodeStatus(data.status || 'SUCCESS');
            setMessage(data.message || 'QR Code recebido.');
            
            if (data.qrcode_base64) {
                setQrCodeImage(`data:image/png;base64,${data.qrcode_base64}`);
            }
        } catch (error) {
            setQrCodeStatus('ERROR');
            const erroApi = error.response?.data?.error || 'Erro ao conectar com o serviço do WhatsApp.';
            setMessage(erroApi);
        }
    };

    const handleDisconnect = async () => {
        setQrCodeStatus('LOADING');
        setMessage('Desconectando WhatsApp...');
        try {
            await api.delete('/api/whatsapp/qrcode/');
            // Após desconectar, tenta buscar novamente para gerar novo QR Code
            fetchQRCode();
        } catch (error) {
            setQrCodeStatus('WORKING');
            setMessage('Erro ao tentar desconectar. Tente novamente.');
        }
    };

    useEffect(() => {
        fetchQRCode();
    }, []);

    return (
        <div className="bg-background-paper border border-white/5 p-6 rounded-xl w-full flex flex-col items-center text-center">
            <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                <span className="text-green-500">📱</span> Integração WhatsApp
            </h3>
            
            <p className="text-sm text-gray-400 mb-6">{message}</p>

            {/* Exibe o QR Code se estiver esperando scannear */}
            {qrCodeStatus === 'WAITING_FOR_SCAN' && qrCodeImage && (
                <div className="flex justify-center mb-6 bg-white p-2 rounded-lg">
                    <img 
                        src={qrCodeImage} 
                        alt="WhatsApp QR Code" 
                        style={{ width: '200px', height: '200px' }}
                    />
                </div>
            )}

            {/* Exibe botão de atualizar caso expire ou demore muito */}
            {['STARTING', 'WAITING_FOR_SCAN', 'ERROR'].includes(qrCodeStatus) && (
                <button 
                    onClick={fetchQRCode}
                    className="w-full bg-background-darker border border-white/10 hover:border-gold text-white font-bold py-2 px-4 rounded-lg transition-all text-sm mt-auto"
                >
                    🔄 Atualizar QR Code
                </button>
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
