module.exports = {
  theme: {
    extend: {
      animation: {
        "gradient": "gradient 8s ease infinite",
        "spin-slow": "spin 20s linear infinite",
      },
      keyframes: {
        gradient: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
    },
  },
}