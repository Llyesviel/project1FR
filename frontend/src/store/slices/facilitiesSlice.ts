import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Facility {
  id: number;
  name: string;
  description: string;
  location: string;
  capacity: number;
  facility_type: string;
  status: 'active' | 'inactive' | 'maintenance';
  created_at: string;
  updated_at: string;
}

export interface Booking {
  id: number;
  facility: number;
  user: number;
  start_time: string;
  end_time: string;
  purpose: string;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  created_at: string;
}

interface FacilitiesState {
  facilities: Facility[];
  bookings: Booking[];
  selectedFacility: Facility | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    search: string;
    type: string;
    status: string;
  };
}

const initialState: FacilitiesState = {
  facilities: [],
  bookings: [],
  selectedFacility: null,
  isLoading: false,
  error: null,
  filters: {
    search: '',
    type: '',
    status: '',
  },
};

const facilitiesSlice = createSlice({
  name: 'facilities',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setFacilities: (state, action: PayloadAction<Facility[]>) => {
      state.facilities = action.payload;
    },
    addFacility: (state, action: PayloadAction<Facility>) => {
      state.facilities.push(action.payload);
    },
    updateFacility: (state, action: PayloadAction<Facility>) => {
      const index = state.facilities.findIndex(f => f.id === action.payload.id);
      if (index !== -1) {
        state.facilities[index] = action.payload;
      }
    },
    deleteFacility: (state, action: PayloadAction<number>) => {
      state.facilities = state.facilities.filter(f => f.id !== action.payload);
    },
    setSelectedFacility: (state, action: PayloadAction<Facility | null>) => {
      state.selectedFacility = action.payload;
    },
    setBookings: (state, action: PayloadAction<Booking[]>) => {
      state.bookings = action.payload;
    },
    addBooking: (state, action: PayloadAction<Booking>) => {
      state.bookings.push(action.payload);
    },
    updateBooking: (state, action: PayloadAction<Booking>) => {
      const index = state.bookings.findIndex(b => b.id === action.payload.id);
      if (index !== -1) {
        state.bookings[index] = action.payload;
      }
    },
    setFilters: (state, action: PayloadAction<Partial<FacilitiesState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearFilters: (state) => {
      state.filters = {
        search: '',
        type: '',
        status: '',
      };
    },
  },
});

export const {
  setLoading,
  setError,
  setFacilities,
  addFacility,
  updateFacility,
  deleteFacility,
  setSelectedFacility,
  setBookings,
  addBooking,
  updateBooking,
  setFilters,
  clearFilters,
} = facilitiesSlice.actions;

export default facilitiesSlice.reducer;