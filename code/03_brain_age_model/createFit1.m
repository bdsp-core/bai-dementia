function [fitresult, gof] = createFit1(x, da)

%% Fit: 'untitled fit 1'.
[xData, yData] = prepareCurveData( x, da );

% Set up fittype and options.
ft = fittype( 'poly3' );
opts = fitoptions( 'Method', 'LinearLeastSquares' );
opts.Robust = 'LAR';

% Fit model to data.
[fitresult, gof] = fit( xData, yData, ft, opts );



