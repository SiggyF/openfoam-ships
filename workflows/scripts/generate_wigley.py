
import numpy as np

def generate_wigley_stl(filename="wigley.stl", L=1.0, B=0.1, T=0.0625, n_x=100, n_z=20):
    """
    Generate a Wigley hull STL file.
    Formula: y = +/- (B/2) * (1 - (2x/L)^2) * (1 - (z/T)^2)
    where x in [-L/2, L/2], z in [-T, 0]
    """
    x = np.linspace(-L/2, L/2, n_x)
    z = np.linspace(-T, 0, n_z)
    X, Z = np.meshgrid(x, z)
    
    # Calculate Y for positive side
    # Ensure arguments are within bounds to avoid negative sqrt issues if using modified formulas
    # Standard Wigley:
    term1 = 1 - (2 * X / L)**2
    term2 = 1 - (Z / T)**2
    
    # Clip to 0 to handle numerical noise at boundaries
    term1 = np.maximum(term1, 0)
    term2 = np.maximum(term2, 0)
    
    Y = (B / 2) * term1 * term2
    
    # Create vertices and faces (quads to triangles)
    vertices = []
    
    # We need to triangulate the grid (X, Y, Z)
    # Strategy: Build two sides (port and starboard) and a deck?
    # Usually for CFD we just need the closed surface.
    # OpenFOAM needs a watertight surface. We need to close the top (deck) and maybe centerline?
    # But Wigley is usually symmetric. We can generate the whole hull.
    
    # Helper to add quad as two triangles
    def add_quad(p1, p2, p3, p4, faces_list):
        faces_list.append([p1, p2, p3])
        faces_list.append([p1, p3, p4])

    faces = []
    
    # Generate points array
    # We will have (n_z, n_x) points for Starboard, same for Port.
    # Starboard: +Y
    # Port: -Y
    
    sb_points = np.zeros((n_z, n_x, 3))
    sb_points[:,:,0] = X
    sb_points[:,:,1] = Y
    sb_points[:,:,2] = Z
    
    pt_points = np.zeros((n_z, n_x, 3))
    pt_points[:,:,0] = X
    pt_points[:,:,1] = -Y
    pt_points[:,:,2] = Z

    def write_stl_triangle(f, v1, v2, v3):
        # Normal calculation
        edge1 = v2 - v1
        edge2 = v3 - v1
        normal = np.cross(edge1, edge2)
        norm_len = np.linalg.norm(normal)
        if norm_len > 1e-6:
            normal /= norm_len
        else:
            normal = np.array([0, 0, 0])
            
        f.write(f"facet normal {normal[0]} {normal[1]} {normal[2]}\n")
        f.write("  outer loop\n")
        f.write(f"    vertex {v1[0]} {v1[1]} {v1[2]}\n")
        f.write(f"    vertex {v2[0]} {v2[1]} {v2[2]}\n")
        f.write(f"    vertex {v3[0]} {v3[1]} {v3[2]}\n")
        f.write("  endloop\n")
        f.write("endfacet\n")

    with open(filename, 'w') as f:
        f.write("solid wigley\n")
        
        # Side shells
        for i in range(n_z - 1):
            for j in range(n_x - 1):
                # Starboard (CCW winding looking from outside)
                # p1(i, j) -> p2(i, j+1) -> p4(i+1, j+1) -> p3(i+1, j)
                # Normal should point OUT (+Y)
                v1 = sb_points[i, j]
                v2 = sb_points[i, j+1]
                v3 = sb_points[i+1, j+1]
                v4 = sb_points[i+1, j]
                write_stl_triangle(f, v1, v2, v3)
                write_stl_triangle(f, v1, v3, v4)
                
                # Port (Normal should point OUT (-Y))
                v1 = pt_points[i, j]
                v2 = pt_points[i+1, j]
                v3 = pt_points[i+1, j+1]
                v4 = pt_points[i, j+1]
                
                write_stl_triangle(f, v1, v2, v3)
                write_stl_triangle(f, v1, v3, v4)
        
        # Transom / Stern ? Wigley is sharp at both ends (Y=0).
        # But top deck (z=0) needs closing.
        # Deck: connect top row (i = n_z - 1) of Port to Starboard?
        # Z is increasing from -T to 0. So deck is at index n_z - 1.
        
        # Deck
        i_deck = n_z - 1
        for j in range(n_x - 1):
            # Connect SB[i_deck, j] to SB[i_deck, j+1]
            # to PT[i_deck, j+1] to PT[i_deck, j]
            # Normal point UP (+Z)
            v1 = sb_points[i_deck, j]
            v2 = sb_points[i_deck, j+1]
            v3 = pt_points[i_deck, j+1] # Y is negative
            v4 = pt_points[i_deck, j]
            
            # v1->v4->v3->v2 ? No.
            # SB (+Y) -> PT (-Y).
            # v1(x, y, 0), v2(x+dx, y', 0)
            # Normal up: v1 -> v2 -> v3
            write_stl_triangle(f, v1, v2, v3)
            write_stl_triangle(f, v1, v3, v4)

        f.write("endsolid wigley\n")
    
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_wigley_stl("config/geometry/wigley.stl")
