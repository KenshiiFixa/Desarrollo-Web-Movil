const mongoose = require('mongoose');

const usuarioSchema = mongoose.Schema({
    rut: String,
    nombres: String,
    apellidos: String,
});

module.exports = mongoose.model('Usuario', usuarioSchema);
