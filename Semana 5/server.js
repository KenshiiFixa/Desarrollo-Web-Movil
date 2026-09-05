const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const { ApolloServer, gql } = require('apollo-server-express');

const Usuario = require('./models/usuario');

mongoose.connect('mongodb://localhost:27017/desarrolloweb');

const typeDefs = gql`
    type Usuario {
        id: ID!
        rut: String!
        nombres: String!
        apellidos: String!
        correoElectronico: String
        telefono: String
        clave: String
        fechaRegistro: String
    }

    input NuevoUsuarioInput {
        rut: String!
        nombres: String!
        apellidos: String!
    }

    type Notificacion {
        detalle: String!
    }

    type Query {
        listarUsuarios: [Usuario]
        buscarUsuarioPorId(id: ID!): Usuario
    }

    type Mutation {
        crearUsuario(input: NuevoUsuarioInput): Usuario
        modificarUsuario(id: ID!, input: NuevoUsuarioInput): Usuario
        borrarUsuario(id: ID!): Notificacion
    }
`;

const resolvers = {
    Query: {
        async listarUsuarios(obj) {
            const usuarios = await Usuario.find();
            return usuarios;
        },
        async buscarUsuarioPorId(obj, { id }) {
            const usuarioEncontrado = await Usuario.findById(id);
            if (usuarioEncontrado === null) {
                return null;
            } else {
                return usuarioEncontrado;
            }
        } 
    },
    Mutation: {
        async crearUsuario(obj, { input }) {
            const usuario = new Usuario(input);
            await usuario.save();
            return usuario;
        },
        async modificarUsuario(_, { id, input }) {
            return await Usuario.findByIdAndUpdate(id, input, { new: true });
        },
        async borrarUsuario(_, { id }) {
            await Usuario.deleteOne({ _id: id });
            return {
                detalle: 'Usuario eliminado exitosamente'
            }
        }
    }
};

let apolloServer = null;
const corsOptions = {
    origin: 'http://localhost:8090',
    credentials: false
};

async function startServer() {
    apolloServer = new ApolloServer({ typeDefs, resolvers, cors: corsOptions });
    await apolloServer.start();
    apolloServer.applyMiddleware({ app, cors: false });
}

startServer();
const app = express();
app.use(cors());
app.listen(8090, function() {
    console.log('Servidor GraphQL iniciado');
})