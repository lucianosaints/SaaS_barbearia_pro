import React from 'react';
import { QRCodeCanvas } from 'qrcode.react';

const PlacaQRCode = React.forwardRef(({ nomeBarbearia, linkAgendamento }, ref) => {
  return (
    <div style={{ position: 'absolute', left: '-9999px', top: 0 }}>
      {/* Container A4 Proportion (210x297mm) -> approx 794x1123px */}
      <div 
        ref={ref}
        className="bg-white flex flex-col items-center justify-between p-12 text-black"
        style={{ width: '794px', height: '1123px' }}
      >
        <div className="text-center mt-24">
          <h1 className="text-6xl font-extrabold mb-4 uppercase tracking-wider">{nomeBarbearia || 'SUA BARBEARIA'}</h1>
          <h2 className="text-4xl font-semibold text-gray-800 mt-6">Agende seu horário online!</h2>
          <p className="text-2xl text-gray-600 mt-6 font-medium">Aponte a câmera do seu celular para o QR Code abaixo</p>
        </div>

        <div className="flex-1 flex items-center justify-center my-12">
          <div className="p-8 border-8 border-black rounded-3xl">
            <QRCodeCanvas 
              value={linkAgendamento || 'https://google.com'} 
              size={400} 
              level={"H"}
            />
          </div>
        </div>

        <div className="mb-12 text-center w-full border-t-2 border-gray-200 pt-8">
          <p className="text-xl text-gray-500 font-medium">criado com barbeiro_Pro</p>
        </div>
      </div>
    </div>
  );
});

export default PlacaQRCode;
