import React, { useState, useEffect, CSSProperties } from 'react';

interface Libro {
  id_libro: number;
  titulo: string;
  autor: string;
  categoria: string;
  ejemplares_disponibles: number;
}

const filtroLabels = ['Género', 'Longitud', 'Disponibilidad', 'Idioma', 'Año'];

const styles = {
  clienteHomeContainer: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    fontFamily: 'Arial, sans-serif',
    alignItems: 'center', 
  } as CSSProperties,

  navbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#4A90E2',
    padding: '10px 20px',
    color: 'white',
    width: '100%', 
    maxWidth: '1440px',
  } as CSSProperties,

  logo: {
    fontSize: '24px',
    fontWeight: 'bold',
    padding: '5px',
    border: '2px solid white',
    marginRight: '20px',
  } as CSSProperties,

  searchBarContainer: {
    flexGrow: 1,
    display: 'flex',
    maxWidth: '600px',
    borderRadius: '4px',
    overflow: 'hidden',
  } as CSSProperties,

  searchInput: {
    flexGrow: 1,
    padding: '10px 15px',
    border: 'none',
    fontSize: '16px',
    backgroundColor: 'white',
  } as CSSProperties,

  searchButton: {
    backgroundColor: '#357ABD',
    color: 'white',
    border: 'none',
    padding: '10px 15px',
    cursor: 'pointer',
    fontSize: '16px',
  } as CSSProperties,

  navIcons: {
    display: 'flex',
    gap: '15px',
    fontSize: '24px',
    cursor: 'pointer',
  } as CSSProperties,

  catalogoContent: {
    display: 'flex',
    flexGrow: 1,
    padding: '20px',
    backgroundColor: '#f5f5f5',
    width: '100%', 
    maxWidth: '1440px', 
  } as CSSProperties,

  // Panel de Filtros
  filtroPanel: {
    width: '200px',
    backgroundColor: '#E0E0E0',
    padding: '15px',
    borderRadius: '4px',
    marginRight: '20px',
    display: 'flex',
    flexDirection: 'column',
  } as CSSProperties,

  filtroPanelHeader: {
    fontSize: '18px',
    marginTop: 0,
    marginBottom: '20px',
    fontWeight: 'bold'
  } as CSSProperties,

  // Botón de filtro
  filtroButton: {
    backgroundColor: '#A9A9A9',
    color: 'black',
    padding: '8px 10px',
    marginBottom: '10px',
    borderRadius: '4px',
    textAlign: 'center',
    cursor: 'pointer',
  } as CSSProperties,

  // Botón de filtro activo
  filtroButtonActive: {
    backgroundColor: '#4A90E2',
    color: 'white',
    padding: '8px 10px',
    marginBottom: '10px',
    borderRadius: '4px',
    textAlign: 'center',
    cursor: 'pointer',
    fontWeight: 'bold',
  } as CSSProperties,

  botonFiltrarBuscar: {
    backgroundColor: '#4A90E2',
    color: 'white',
    border: 'none',
    padding: '10px',
    marginTop: 'auto',
    cursor: 'pointer',
    borderRadius: '4px',
    fontWeight: 'bold',
  } as CSSProperties,

  // GRID del Catálogo
  catalogoGrid: {
    flexGrow: 1,
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '20px',
  } as CSSProperties,

  // Tarjeta de Libro
  tarjetaLibro: {
    backgroundColor: 'white',
    borderRadius: '4px',
    overflow: 'hidden',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    display: 'flex',
    flexDirection: 'column',
    minHeight: '320px',
  } as CSSProperties,

  tarjetaImagen: {
    backgroundColor: '#D3D3D3',
    height: '180px',
    width: '100%',
  } as CSSProperties,

  tarjetaInfo: {
    padding: '10px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    flexGrow: 1,
    justifyContent: 'space-between'
  } as CSSProperties,

  tarjetaTitulo: {
    fontWeight: 'bold',
    marginBottom: '5px',
    fontSize: '1.1em'
  } as CSSProperties,

  tarjetaAutor: {
    fontSize: '0.9em',
    color: '#666',
    marginBottom: '10px',
  } as CSSProperties,

  disponibilidadTexto: (isAvailable: boolean): CSSProperties => ({
    fontSize: '0.8em',
    fontWeight: 'bold',
    color: isAvailable ? 'green' : 'red',
    marginBottom: '5px'
  }),

  botonAgregar: {
    backgroundColor: '#4A90E2',
    color: 'white',
    border: 'none',
    padding: '8px 15px',
    cursor: 'pointer',
    borderRadius: '4px',
    fontWeight: 'bold',
    fontSize: '0.8em',
    width: '90%',
  } as CSSProperties,

  errorMessage: {
    color: 'red',
    fontWeight: 'bold',
    gridColumn: '1 / -1',
    padding: '20px',
    textAlign: 'center'
  } as CSSProperties,
};

const TarjetaLibro: React.FC<{
  libro: Libro;
  onAgregar: (libro: Libro) => void;
}> = ({ libro, onAgregar }) => {
  const isAvailable = libro.ejemplares_disponibles > 0;

  return (
    <div style={styles.tarjetaLibro}>
      <div style={styles.tarjetaImagen}></div>

      <div style={styles.tarjetaInfo}>
        <div>
          <div style={styles.tarjetaTitulo}>{libro.titulo.toUpperCase()}</div>
          <div style={styles.tarjetaAutor}>{libro.autor}</div>
          <div style={styles.disponibilidadTexto(isAvailable)}>
            {isAvailable ? `Disponible (${libro.ejemplares_disponibles})` : 'Agotado'}
          </div>
        </div>
        <button
          style={styles.botonAgregar}
          disabled={!isAvailable}
          onClick={() => onAgregar(libro)}
        >
          AGREGAR
        </button>
      </div>
    </div>
  );
};

export default function ClienteHome() {
  const [libros, setLibros] = useState<Libro[]>([]);
  const [busqueda, setBusqueda] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtroActivo, setFiltroActivo] = useState<string | null>(null); 

  const API_BASE_URL = "http://127.0.0.1:5000/api";

  useEffect(() => {
    fetchLibros();
  }, []);

  const fetchLibros = async (queryString = '') => {
    setIsLoading(true);
    setError(null);
    
    const fullUrl = `${API_BASE_URL}/libros${queryString.startsWith('?') ? queryString : (queryString ? `?q=${encodeURIComponent(queryString)}` : '')}`;
    
    try {
      const response = await fetch(fullUrl);
      if (!response.ok) {
        // Mejor manejo de errores HTTP
        const errorDetail = response.status === 500 ? 'INTERNAL SERVER ERROR (Verifica la consola del backend)' : response.statusText;
        throw new Error(`Error al cargar datos: ${errorDetail}`);
      }
      const data = await response.json();
      if (data.ok) {
        setLibros(data.items as Libro[]);
      } else {
        throw new Error(data.error || "Error desconocido en la API.");
      }
    } catch (err) {
      console.error("Error fetching libros:", err);
      setError(`No se pudieron cargar los libros. Detalle: ${(err as Error).message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLibros(busqueda);
  };

  const handleAgregarClick = (libro: Libro) => {
    if (libro.ejemplares_disponibles > 0) {
      alert(`✅ Solicitud de préstamo/reserva para "${libro.titulo}" enviada.`);

    } else {
      alert(`⚠️ "${libro.titulo}" no tiene ejemplares disponibles.`);
    }
  };

  const handleFiltrarBuscar = () => {
    if (filtroActivo === 'Género' && busqueda.trim() !== '') {
        fetchLibros(`?categoria=${encodeURIComponent(busqueda)}`);
        alert(`🔍 Buscando libros con categoría: "${busqueda}"`);
        return;
    }
    
    fetchLibros(busqueda);
    if (busqueda.trim() !== '') {
      alert(`🔍 Buscando por título/autor/ISBN: "${busqueda}"`);
    } else if (!filtroActivo) {
        alert('Cargando todos los libros sin búsqueda específica ni filtros.');
    } else {
        alert(`Filtro activo (${filtroActivo}), pero no implementado en la API aún. Ejecutando búsqueda general.`);
    }
  };

  return (
    <main style={styles.clienteHomeContainer}>

      {/* NAV BAR */}
      <header style={styles.navbar}>
        <div style={styles.logo}>BEC</div>

        <form style={styles.searchBarContainer} onSubmit={handleSearchSubmit}>
          <input
            type="text"
            placeholder="Buscar por título, autor, ..."
            style={styles.searchInput}
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
          />
          <button type="submit" style={styles.searchButton}>
            🔍
          </button>
        </form>

        <div style={styles.navIcons}>
          <span style={{ cursor: 'pointer' }}>👤</span>
          <span style={{ cursor: 'pointer' }}>🛒</span>
        </div>
      </header>

      <div style={styles.catalogoContent}>
        {/* PANEL DE FILTROS */}
        <aside style={styles.filtroPanel}>
          <h2 style={styles.filtroPanelHeader}>Filtros</h2>

          {filtroLabels.map(filtro => (
            <div
              key={filtro}
              style={filtroActivo === filtro ? styles.filtroButtonActive : styles.filtroButton}
              onClick={() => setFiltroActivo(filtro === filtroActivo ? null : filtro)} // Toggle
            >
              {filtro}
            </div>
          ))}

          <button
            style={styles.botonFiltrarBuscar}
            onClick={handleFiltrarBuscar}
          >
            Filtrar y Buscar
          </button>
        </aside>

        {/* GRID DEL CATÁLOGO */}
        <section style={styles.catalogoGrid}>
          {isLoading ? (
            <p style={{ gridColumn: '1 / -1', textAlign: 'center' }}>Cargando libros...</p>
          ) : error ? (
            <p style={styles.errorMessage}>❌ {error}</p>
          ) : libros.length > 0 ? (
            libros.map(libro => (
              <TarjetaLibro
                key={libro.id_libro}
                libro={libro}
                onAgregar={handleAgregarClick}
              />
            ))
          ) : (
            <p style={{ gridColumn: '1 / -1', textAlign: 'center' }}>No se encontraron libros que coincidan con la búsqueda.</p>
          )}
        </section>
      </div>
    </main>
  );
}
