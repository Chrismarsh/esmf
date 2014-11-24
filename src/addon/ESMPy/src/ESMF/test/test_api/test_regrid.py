"""
regrid unit test file
"""

from ESMF import *
from ESMF.test.base import TestBase
from ESMF.test.test_api.mesh_utilities import *
from ESMF.test.test_api.grid_utilities import *

class TestRegrid(TestBase):
    def test_field_regrid(self):
        # create grids
        max_index = np.array([20, 20])
        srcgrid = Grid(max_index, coord_sys=CoordSys.CART)
        max_index = np.array([25, 25])
        dstgrid = Grid(max_index, coord_sys=CoordSys.CART)

        # Add coordinates
        srcgrid.add_coords()
        dstgrid.add_coords()

        [x, y] = [0, 1]
        gridXCorner = srcgrid.get_coords(x)
        gridYCorner = srcgrid.get_coords(y)

        for i in xrange(gridXCorner.shape[x]):
            gridXCorner[i, :] = float(i) / 6.

        for j in xrange(gridYCorner.shape[y]):
            gridYCorner[:, j] = float(j) / 6.

        gridXCorner = dstgrid.get_coords(x)
        gridYCorner = dstgrid.get_coords(y)

        for i in xrange(gridXCorner.shape[x]):
            gridXCorner[i, :] = float(i) / 4.

        for j in xrange(gridYCorner.shape[y]):
            gridYCorner[:, j] = float(j) / 4.

        # create a Field on the Grid
        srcfield = NewField(srcgrid, "GRIDFIELD!")
        srcfield.data[:, :] = 10.
        dstfield = NewField(srcgrid, "GRIDFIELD!")
        dstfield.data[:, :] = 10.

        # regridding
        rh = Regrid(srcfield, dstfield, regrid_method=RegridMethod.BILINEAR)
        dstfield = rh(srcfield, dstfield)

    def test_field_regrid_gridmesh(self):
        # create mesh
        parallel = False
        if pet_count() > 1:
            if pet_count() > 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        mesh = None
        if parallel:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50()
        dstfield = NewField(mesh, 'MESHFIELD!', meshloc=MeshLoc.ELEMENT)

        # create grid
        max_index = np.array([16, 16])
        grid = Grid(max_index, coord_sys=CoordSys.CART)

        # Add coordinates
        grid.add_coords(staggerloc=[StaggerLoc.CENTER, StaggerLoc.CORNER])

        [x, y] = [0, 1]
        gridXCorner = grid.get_coords(x, staggerloc=StaggerLoc.CORNER)
        gridYCorner = grid.get_coords(y, staggerloc=StaggerLoc.CORNER)

        for i in xrange(gridXCorner.shape[x]):
            gridXCorner[i, :] = float(i)

        for j in xrange(gridYCorner.shape[y]):
            gridYCorner[:, j] = float(j)

        # create a Field on the Grid
        srcfield = NewField(grid, "GRIDFIELD!")

        srcfield.data[:, :] = 10.

        # regridding
        rh = Regrid(srcfield, dstfield, regrid_method=RegridMethod.CONSERVE)
        dstfield = rh(srcfield, dstfield)

    def test_field_regrid_zeroregion(self):
        # create mesh
        parallel = False
        if pet_count() > 1:
            if pet_count() > 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        mesh = None
        if parallel:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50()

        # create a field on the mesh
        srcfield = NewField(mesh, 'MESHFIELD!', meshloc=MeshLoc.ELEMENT)

        # initialize the source field
        for i in range(srcfield.shape[0]):
            srcfield.data[i] = 20.0

        # create grid
        grid = grid_create([0, 0, 8, 8], [0, 0, 4, 4], domask=True)

        [x, y] = [0, 1]

        # create a Field on the Grid
        dstfield = NewField(grid, "GRIDFIELD!", mask_values=[0])

        # initialize the destination field according to the mask
        dstfield.data[:, :] = -100

        # regridding
        rh = Regrid(srcfield, dstfield, regrid_method=RegridMethod.CONSERVE,
                    dst_mask_values=np.array([0]))
        dstfield = rh(srcfield, dstfield, zero_region=Region.SELECT)

        # validate that the masked values were not zeroed out
        for i in range(dstfield.mask.shape[x]):
            for j in range(dstfield.mask.shape[y]):
                if dstfield.mask[i, j] == True:
                    assert(dstfield[i, j] == 0)

    def test_field_regrid_area(self):
        # create mesh
        parallel = False
        if pet_count() > 1:
            if pet_count() > 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        mesh = None
        if parallel:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50()

        # create grid
        grid = grid_create([0, 0, 8, 8], [0, 0, 4, 4], doarea=True)

        [x, y] = [0, 1]

        # create area field
        dstarea = NewField(mesh, 'DESTINATION AREAS!',
                           meshloc=MeshLoc.ELEMENT)
        dstarea.get_area()

        # create a Field on the Grid
        srcarea = NewField(grid, "SOURCE AREAS!")
        srcarea.get_area()

        for i in range(srcarea.shape[x]):
            for j in range(srcarea.shape[y]):
                if (srcarea[i, j] != 5):
                    print "Cell area is {0}, but expected 5".format(srcarea[i, j])

        # subtract two because the last two cells of mesh are triangles with half area
        for i in range(dstarea.shape[0]):
            if (dstarea[i] != 0.25):
                assert (dstarea[i] == 0.125)

    def test_field_regrid_periodic(self):
        esmp = ESMF.Manager(logkind=ESMF.LogKind.MULTI, debug=True)

        parallel = False
        if ESMF.pet_count() > 1:
            if ESMF.pet_count() != 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        # create a grid
        srcgrid = grid_create_periodic([60, 30], domask=True)
        dstgrid = grid_create_periodic([55, 28])

        # create the Fields
        srcfield = ESMF.NewField(srcgrid, 'srcfield', mask_values=[0])
        dstfield = ESMF.NewField(dstgrid, 'dstfield')
        exactfield = ESMF.NewField(dstgrid, 'exactfield')

        # create the area fields
        srcareafield = ESMF.NewField(srcgrid, 'srcareafield')
        dstareafield = ESMF.NewField(dstgrid, 'dstareafield')

        # create the fraction fields
        srcfracfield = ESMF.NewField(srcgrid, 'srcfracfield')
        dstfracfield = ESMF.NewField(dstgrid, 'dstfracfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid_periodic(srcfield)
        exact_field = initialize_field_grid_periodic(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = ESMF.Regrid(srcfield, dstfield,
                                    src_mask_values=np.array([0]),
                                    regrid_method=ESMF.RegridMethod.CONSERVE,
                                    unmapped_action=ESMF.UnmappedAction.ERROR,
                                    src_frac_field=srcfracfield,
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_grid(srcfield, srcareafield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield, dstareafield)

        # compare results and output PASS or FAIL
        compare_fields_grid(dstfield, exact_field, 10E-2, 10e-15, parallel=parallel,
                            dstfracfield=dstfracfield, mass1=srcmass, mass2=dstmass)

    def test_grid_grid_regrid_csrv_mask_3D(self):
        esmp = ESMF.Manager(logkind=ESMF.LogKind.MULTI, debug=True)

        parallel = False
        if ESMF.pet_count() > 1:
            if ESMF.pet_count() != 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        # create a grid
        srcgrid = grid_create_3d([0, 0, 0, 21, 21, 21], [0, 0, 0, 21, 21, 21])
        dstgrid = grid_create_3d([0.5, 0.5, 0.5, 19.5, 19.5, 19.5], \
                                 [0.5, 0.5, 0.5, 19.5, 19.5, 19.5])

        # create Field objects on the Meshes
        srcfield = ESMF.NewField(srcgrid, 'srcfield')
        srcareafield = ESMF.NewField(srcgrid, 'srcareafield')
        srcfracfield = ESMF.NewField(srcgrid, 'srcfracfield')
        dstfield = ESMF.NewField(dstgrid, 'dstfield')
        dstareafield = ESMF.NewField(dstgrid, 'dstareafield')
        dstfracfield = ESMF.NewField(dstgrid, 'dstfracfield')
        exactfield = ESMF.NewField(dstgrid, 'exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid_3d(srcfield)
        exactfield = initialize_field_grid_3d(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = ESMF.Regrid(srcfield, dstfield, \
                                    regrid_method=ESMF.RegridMethod.CONSERVE, \
                                    unmapped_action=ESMF.UnmappedAction.ERROR, \
                                    src_frac_field=srcfracfield, \
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_grid(srcfield, srcareafield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield, dstareafield)

        # compare results and output PASS or FAIL
        compare_fields_grid(dstfield, exactfield, 10E-03, 10E-16, parallel=parallel,
                            dstfracfield=dstfracfield, mass1=srcmass, mass2=dstmass)

    def test_grid_grid_regrid_csrv_mask(self):
        esmp = ESMF.Manager(logkind=ESMF.LogKind.MULTI, debug=True)

        parallel = False
        if ESMF.pet_count() > 1:
            if ESMF.pet_count() != 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        # create two unique Grid objects
        srcgrid = grid_create([0, 0, 21, 21], [0, 0, 21, 21], domask=True)
        dstgrid = grid_create([0.5, 0.5, 19.5, 19.5], [0.5, 0.5, 19.5, 19.5])

        # create Field objects on the Meshes
        srcfield = ESMF.NewField(srcgrid, 'srcfield', mask_values=[0])
        srcareafield = ESMF.NewField(srcgrid, 'srcareafield')
        srcfracfield = ESMF.NewField(srcgrid, 'srcfracfield')
        dstfield = ESMF.NewField(dstgrid, 'dstfield')
        dstareafield = ESMF.NewField(dstgrid, 'dstareafield')
        dstfracfield = ESMF.NewField(dstgrid, 'dstfracfield')
        exactfield = ESMF.NewField(dstgrid, 'exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_grid(srcfield)
        dstfield2 = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = ESMF.Regrid(srcfield, dstfield, \
                                    src_mask_values=np.array([0]), \
                                    regrid_method=ESMF.RegridMethod.CONSERVE, \
                                    unmapped_action=ESMF.UnmappedAction.ERROR, \
                                    src_frac_field=srcfracfield, \
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_grid(srcfield, srcareafield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield, dstareafield)

        # compare results and output PASS or FAIL
        compare_fields_grid(dstfield, dstfield2, 10E-3, 10E-16, parallel=parallel,
                            dstfracfield=dstfracfield, mass1=srcmass, mass2=dstmass)

    def test_grid_mesh_regrid_csrv_mask(self):
        esmp = ESMF.Manager(logkind=ESMF.LogKind.MULTI, debug=True)

        parallel = False
        if ESMF.pet_count() > 1:
            if ESMF.pet_count() != 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        # create a Mesh
        if parallel:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, elemMask, elemArea = \
                mesh_create_50_parallel(domask=True, doarea=True)
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn, elemMask, elemArea = \
                mesh_create_50(domask=True, doarea=True)

        # create a grid
        grid = grid_create([0, 0, 8, 8], [0, 0, 4, 4], doarea=True)

        # create Field objects on the Meshes
        srcfield = ESMF.NewField(mesh, 'srcfield', meshloc=ESMF.MeshLoc.ELEMENT)
        srcfracfield = ESMF.NewField(mesh, 'srcfracfield', meshloc=ESMF.MeshLoc.ELEMENT)
        srcareafield = ESMF.NewField(mesh, 'srcareafield', meshloc=ESMF.MeshLoc.ELEMENT)

        # make gridded fields
        exactfield = ESMF.NewField(grid, 'exactfield')
        dstfield = ESMF.NewField(grid, 'dstfield')
        dstfracfield = ESMF.NewField(grid, 'dstfracfield')
        dstareafield = ESMF.NewField(grid, 'dstareafield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn,
                                         domask=True, elemMask=elemMask)
        exactfield = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = ESMF.Regrid(srcfield, dstfield, \
                                    src_mask_values=np.array([0]), \
                                    regrid_method=ESMF.RegridMethod.CONSERVE, \
                                    unmapped_action=ESMF.UnmappedAction.ERROR, \
                                    src_frac_field=srcfracfield, \
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_mesh(srcfield, srcareafield, dofrac=True,
                                    fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield, dstareafield)

        # compare results and output PASS or FAIL
        compare_fields_grid(dstfield, exactfield, 80E-1, 10E-15, parallel=parallel,
                            dstfracfield=dstfracfield, mass1=srcmass, mass2=dstmass)

    def test_grid_mesh_regrid_csrv(self):
        esmp = ESMF.Manager(logkind=ESMF.LogKind.MULTI, debug=True)

        parallel = False
        if ESMF.pet_count() > 1:
            if ESMF.pet_count() != 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        # create a Mesh
        if parallel:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50()

        # create a grid
        grid = grid_create([0, 0, 8, 8], [0, 0, 4, 4])

        # create Fields
        srcfield = ESMF.NewField(mesh, 'srcfield', meshloc=ESMF.MeshLoc.ELEMENT)
        srcareafield = ESMF.NewField(mesh, 'srcareafield', meshloc=ESMF.MeshLoc.ELEMENT)
        srcfracfield = ESMF.NewField(mesh, 'srcfracfield', meshloc=ESMF.MeshLoc.ELEMENT)
        dstfield = ESMF.NewField(grid, 'dstfield')
        dstareafield = ESMF.NewField(grid, 'dstareafield')
        dstfracfield = ESMF.NewField(grid, 'dstfracfield')
        exactfield = ESMF.NewField(grid, 'exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        exactfield = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = ESMF.Regrid(srcfield, dstfield,
                                    regrid_method=ESMF.RegridMethod.CONSERVE,
                                    unmapped_action=ESMF.UnmappedAction.ERROR, \
                                    src_frac_field=srcfracfield, \
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_mesh(srcfield, srcareafield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_grid(dstfield, dstareafield)

        # compare results and output PASS or FAIL
        compare_fields_grid(dstfield, exactfield, 50E-1, 10E-16, parallel=parallel,
                            dstfracfield=dstfracfield, mass1=srcmass, mass2=dstmass)

    def test_grid_mesh_regrid_mask(self):
        esmp = ESMF.Manager(logkind=ESMF.LogKind.MULTI, debug=True)

        parallel = False
        if ESMF.pet_count() > 1:
            if ESMF.pet_count() != 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        # create a grid
        grid = grid_create([0, 0, 8, 8], [0, 0, 4, 4], domask=True)

        # create a Mesh
        if parallel:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50()

        # create Field objects
        srcfield = ESMF.NewField(mesh, 'srcfield')
        dstfield = ESMF.NewField(grid, 'dstfield', mask_values=[0])
        exactfield = ESMF.NewField(grid, 'exactfield', mask_values=[0])

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        exactfield = initialize_field_grid(exactfield, domask=True)

        # run the ESMF regridding
        regridSrc2Dst = ESMF.Regrid(srcfield, dstfield,
                                    dst_mask_values=np.array([0]), \
                                    regrid_method=ESMF.RegridMethod.BILINEAR,
                                    unmapped_action=ESMF.UnmappedAction.IGNORE)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compare results and output PASS or FAIL
        compare_fields_grid(dstfield, exactfield, 20E-1, 10E-16, parallel=parallel,
                            regrid_method=ESMF.RegridMethod.BILINEAR)

    def test_grid_mesh_regrid(self):
        esmp = ESMF.Manager(logkind=ESMF.LogKind.MULTI, debug=True)

        parallel = False
        if ESMF.pet_count() > 1:
            if ESMF.pet_count() != 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        # create a grid
        grid = grid_create([0, 0, 8, 8], [0, 0, 4, 4])

        # create a Mesh
        if parallel:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50_parallel()
        else:
            mesh, nodeCoord, nodeOwner, elemType, elemConn = \
                mesh_create_50()

        # create Field objects
        srcfield = ESMF.NewField(mesh, 'srcfield')
        dstfield = ESMF.NewField(grid, 'dstfield')
        exactfield = ESMF.NewField(grid, 'exactfield')

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoord, nodeOwner, elemType, elemConn)
        exactfield = initialize_field_grid(exactfield)

        # run the ESMF regridding
        regridSrc2Dst = ESMF.Regrid(srcfield, dstfield,
                                    regrid_method=ESMF.RegridMethod.BILINEAR,
                                    unmapped_action=ESMF.UnmappedAction.ERROR)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compare results and output PASS or FAIL
        compare_fields_grid(dstfield, exactfield, 40E-2, 10E-16, parallel=parallel,
                            regrid_method=ESMF.RegridMethod.BILINEAR)

    def test_mesh_mesh_regrid(self):
        esmp = ESMF.Manager(logkind=ESMF.LogKind.MULTI, debug=True)

        parallel = False
        if ESMF.pet_count() > 1:
            if ESMF.pet_count() > 4:
                raise NameError('MPI rank must be 4 in parallel mode!')
            parallel = True

        # create two unique Mesh objects
        if parallel:
            srcmesh, nodeCoordSrc, nodeOwnerSrc, elemTypeSrc, elemConnSrc = \
                mesh_create_5_parallel()
            dstmesh, nodeCoordDst, nodeOwnerDst, elemTypeDst, elemConnDst = \
                mesh_create_10_parallel()
        else:
            srcmesh, nodeCoordSrc, nodeOwnerSrc, elemTypeSrc, elemConnSrc = \
                mesh_create_5()
            dstmesh, nodeCoordDst, nodeOwnerDst, elemTypeDst, elemConnDst = \
                mesh_create_10()

        # create ESMP_Field objects on the Meshes
        srcfield = ESMF.NewField(srcmesh, 'srcfield', meshloc=ESMF.MeshLoc.ELEMENT)
        srcareafield = ESMF.NewField(srcmesh, 'srcareafield', meshloc=ESMF.MeshLoc.ELEMENT)
        srcfracfield = ESMF.NewField(srcmesh, 'srcfracfield', meshloc=ESMF.MeshLoc.ELEMENT)
        dstfield = ESMF.NewField(dstmesh, 'dstfield', meshloc=ESMF.MeshLoc.ELEMENT)
        dstareafield = ESMF.NewField(dstmesh, 'dstareafield', meshloc=ESMF.MeshLoc.ELEMENT)
        dstfracfield = ESMF.NewField(dstmesh, 'dstfracfield', meshloc=ESMF.MeshLoc.ELEMENT)
        exactfield = ESMF.NewField(dstmesh, 'exactfield', meshloc=ESMF.MeshLoc.ELEMENT)

        # initialize the Fields to an analytic function
        srcfield = initialize_field_mesh(srcfield, nodeCoordSrc, nodeOwnerSrc, \
                                         elemTypeSrc, elemConnSrc)
        exactfield = initialize_field_mesh(exactfield, nodeCoordDst, nodeOwnerDst, \
                                           elemTypeDst, elemConnDst)

        # run the ESMF regridding
        regridSrc2Dst = ESMF.Regrid(srcfield, dstfield,
                                    regrid_method=ESMF.RegridMethod.CONSERVE,
                                    unmapped_action=ESMF.UnmappedAction.ERROR, \
                                    src_frac_field=srcfracfield, \
                                    dst_frac_field=dstfracfield)
        dstfield = regridSrc2Dst(srcfield, dstfield)

        # compute the mass
        srcmass = compute_mass_mesh(srcfield, srcareafield,
                                    dofrac=True, fracfield=srcfracfield)
        dstmass = compute_mass_mesh(dstfield, dstareafield)

        # compare results and output PASS or FAIL
        compare_fields_mesh(dstfield, exactfield, 10E-2, 10E-16, parallel=parallel,
                            dstfracfield=dstfracfield, mass1=srcmass, mass2=dstmass)