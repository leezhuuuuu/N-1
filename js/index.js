const app = require('./server');
const routes = require('./routes');

app.use('/', routes);

const PORT = process.env.PORT || 18888;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server is running on port ${PORT}`);
}); 