! $Id: ESMF_StateGet.cpp,v 1.4 2004/06/08 09:27:21 nscollins Exp $
!
! Earth System Modeling Framework
! Copyright 2002-2003, University Corporation for Atmospheric Research, 
! Massachusetts Institute of Technology, Geophysical Fluid Dynamics 
! Laboratory, University of Michigan, National Centers for Environmental 
! Prediction, Los Alamos National Laboratory, Argonne National Laboratory, 
! NASA Goddard Space Flight Center.
! Licensed under the GPL.
!
!==============================================================================
^define ESMF_FILENAME "ESMF_StateGet.F90"
!
!     ESMF StateGet module
      module ESMF_StateGetMod
!
!==============================================================================
!
! This file contains the State class methods which are automatically
!  generated from macros to handle the type/kind/rank overloading.
!  See ESMF_State.F90 for non-macroized entry points.
! class methods.
!
!------------------------------------------------------------------------------
! INCLUDES
! < ignore blank lines below.  they are created by the files which
!   define various macros. >
#include "ESMF_StateMacros.h"
^include "ESMF.h"
!------------------------------------------------------------------------------
! !USES:
      use ESMF_BaseTypesMod
      use ESMF_BaseMod
      use ESMF_LogErrMod
      use ESMF_LocalArrayMod
      use ESMF_ArrayMod
      use ESMF_ArrayGetMod
      use ESMF_FieldMod
      use ESMF_BundleMod
      use ESMF_StateMod
      implicit none

!------------------------------------------------------------------------------
! !PRIVATE TYPES:
      private

!------------------------------------------------------------------------------
! !PUBLIC MEMBER FUNCTIONS:

      public ESMF_StateGetDataPointer
 
!EOP
!------------------------------------------------------------------------------
! The following line turns the CVS identifier string into a printable variable.
      character(*), parameter, private :: version = &
      '$Id: ESMF_StateGet.cpp,v 1.4 2004/06/08 09:27:21 nscollins Exp $'

!==============================================================================
! 
! INTERFACE BLOCKS
!
!==============================================================================


!------------------------------------------------------------------------------

!BOP
! !IROUTINE: ESMF_StateGetDataPointer -- Get an F90 pointer to the data contents

! !INTERFACE:
     interface ESMF_StateGetDataPointer

! !PRIVATE MEMBER FUNCTIONS:
!
      ! < declarations of interfaces for each T/K/R >
InterfaceMacro(StateGetDataPointer)

! !DESCRIPTION: 
! This interface provides a single entry point for the various 
!  types of {\tt ESMF\_StateGetDataPointer} subroutines.   
!  
!EOP 
end interface

!==============================================================================

      contains

!==============================================================================

!------------------------------------------------------------------------------
!------------------------------------------------------------------------------

      ! < declarations of subroutines for each T/K/R >
DeclarationMacro(StateGetDataPointer)


        end module ESMF_StateGetMod

