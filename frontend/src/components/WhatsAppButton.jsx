import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export default function WhatsAppButton() {
  const [isHovered, setIsHovered] = useState(false);
  const phoneNumber = '5521998301041';
  const message = 'Olá! Gostaria de saber mais sobre o sistema Salão Pro.';
  const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`;

  return (
    <div 
      className="fixed bottom-6 right-6 z-50 flex items-center gap-3"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <AnimatePresence>
        {isHovered && (
          <motion.div
            initial={{ opacity: 0, x: 20, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 20, scale: 0.9 }}
            transition={{ duration: 0.2 }}
            className="bg-[#25D366] text-white px-5 py-2.5 rounded-full font-semibold shadow-lg text-sm whitespace-nowrap hidden sm:block"
          >
            Fale com a i9builder
          </motion.div>
        )}
      </AnimatePresence>

      <a
        href={whatsappUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="w-[60px] h-[60px] bg-[#25D366] rounded-[18px] flex items-center justify-center shadow-2xl hover:scale-105 transition-transform duration-300"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-10 h-10 text-white"
        >
          <path
            fillRule="evenodd"
            d="M12.012 2C6.494 2 2 6.495 2 12.012c0 1.77.466 3.498 1.348 5.01L2 22l5.127-1.343A9.972 9.972 0 0012.012 22c5.517 0 9.999-4.495 9.999-10.012S17.529 2 12.012 2zm5.405 14.475c-.23.649-1.33 1.25-1.831 1.312-.486.06-1.127.185-3.593-.837-2.953-1.226-4.838-4.24-4.981-4.43-.142-.192-1.189-1.583-1.189-3.02 0-1.437.75-2.146 1.018-2.433.268-.287.585-.359.779-.359.194 0 .388.003.559.01.18.008.423-.071.657.493.245.592.837 2.04.912 2.19.074.15.124.327.026.519-.098.192-.148.312-.295.485-.148.172-.313.376-.445.49-.142.122-.293.26-.129.544.164.285.73 1.209 1.564 1.95.1.09.201.176.305.258.852.668 1.72 1.054 2.038 1.157.318.102.502.086.69-.13.189-.215.81-1.144 1.01-1.35.201-.205.402-.172.67-.07.268.103 1.696.8 1.986.945.29.145.483.217.553.337.071.12.071.693-.159 1.342z"
            clipRule="evenodd"
          />
        </svg>
      </a>
    </div>
  );
}
