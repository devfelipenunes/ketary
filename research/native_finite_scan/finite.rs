// Research only. Caller owns the immutable contiguous f64 buffer.
#[no_mangle]
pub unsafe extern "C" fn finite_scan(data: *const f64, n: usize) -> i32 {
    if n == 0 { return 1; }
    let values = unsafe { std::slice::from_raw_parts(data, n) };
    let mut valid = true;
    for &value in values {
        valid &= value.is_finite();
    }
    valid as i32
}
